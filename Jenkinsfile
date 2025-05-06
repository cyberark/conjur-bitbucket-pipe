#!/usr/bin/env groovy

@Library("product-pipelines-shared-library") _

// Automated release, promotion and dependencies
properties([
  // Include the automated release parameters for the build
  release.addParams(),
  // Dependencies of the project that should trigger builds
  dependencies([
    'conjur-enterprise/conjur-api-python'
  ])
])

// Performs release promotion.  No other stages will be run
if (params.MODE == "PROMOTE") {
  release.promote(params.VERSION_TO_PROMOTE) { infrapool, sourceVersion, targetVersion, assetDirectory ->
    // Any assets from sourceVersion Github release are available in assetDirectory
    // Any version number updates from sourceVersion to targetVersion occur here
    // Any publishing of targetVersion artifacts occur here
    // Anything added to assetDirectory will be attached to the Github Release

    runSecurityScans(infrapool,
      image: "registry.tld/conjur-bitbucket-pipe:${sourceVersion}",
      buildMode: params.MODE,
      branch: env.BRANCH_NAME)

    // Pull existing images from internal registry in order to promote
    infrapool.agentSh """
      export PATH="release-tools/bin:${PATH}"
      docker pull registry.tld/conjur-bitbucket-pipe:${sourceVersion}
      # Promote source version to target version.
      ./bin/publish.sh --promote --source ${sourceVersion} --target ${targetVersion}
    """

    dockerImages = "docker-image*.tar"
    // Place the Docker image(s) onto the Jenkins agent and sign them
    infrapool.agentGet from: "${assetDirectory}/${dockerImages}", to: "./"
    signArtifacts patterns: ["${dockerImages}"]
    // Copy the docker images and signed artifacts (.sig) back to
    // infrapool and into the assetDirectory for release promotion
    dockerImageLocation = pwd() + "/docker-image*.tar*"
    infrapool.agentPut from: "${dockerImageLocation}", to: "${assetDirectory}"
    // Resolve ownership issue before promotion
    sh 'git config --global --add safe.directory ${PWD}'
  }
  release.copyEnterpriseRelease(params.VERSION_TO_PROMOTE)

  // Fetch the SSH key for the Bitbucket account from Conjur,
  // and use it push to the Bitbucket repository. Update the
  // 'main' branch and the version tag.
  sh """
  summon --yaml 'SSH_KEY: !var ci/bitbucket/ssh-key' bash -c 'echo $SSH_KEY > bitbucket-key'
  chmod 600 bitbucket-key
  ssh-add bitbucket-key

  source_ref=\$(git rev-parse --abbrev-ref HEAD)
  dest_ref="refs/heads/main"
  dest_tag="refs/tags/v${params.VERSION_TO_PROMOTE}"
  bitbucket_repo="git@bitbucket.org:cyberark-conjur/conjur-bitbucket-pipe.git"

  git push -f ${bitbucket_repo} ${source_ref}:${dest_ref}
  git push -f ${bitbucket_repo} ${source_ref}:${dest_tag}
  
  rm bitbucket-key
  """

  return
}

pipeline {
  agent { label 'conjur-enterprise-common-agent' }

  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '30'))
  }

  triggers {
    cron(getDailyCronString())
  }

  environment {
    // Sets the MODE to the specified or autocalculated value as appropriate
    MODE = release.canonicalizeMode()
  }

  stages {
    // Aborts any builds triggered by another project that wouldn't include any changes
    stage ("Skip build if triggering job didn't create a release") {
      when {
        expression {
          MODE == "SKIP"
        }
      }
      steps {
        script {
          currentBuild.result = 'ABORTED'
          error("Aborting build because this build was triggered from upstream, but no release was built")
        }
      }
    }

    stage('Scan for internal URLs') {
      steps {
        script {
          detectInternalUrls()
        }
      }
    }

    stage('Get InfraPool ExecutorV2 Agent(s)') {
      steps{
        script {
          // Request ExecutorV2 agents for 1 hour
          infrapool = getInfraPoolAgent.connected(type: "ExecutorV2", quantity: 1, duration: 1)[0]
        }
      }
    }

    // Generates a VERSION file based on the current build number and latest version in CHANGELOG.md
    stage('Validate Changelog and set version') {
      steps {
        script {
          updateVersion(infrapool, "CHANGELOG.md", "${BUILD_NUMBER}")
        }
      }
    }

    stage('Build') {
      stages {
        stage('Build Docker Image') {
          steps {
            script {
              infrapool.agentSh './bin/build.sh'
            }
          }
        }
        stage('Push images to internal registry') {
          steps {
            script {
              infrapool.agentSh './bin/publish.sh --internal'
            }
          }
        }
        stage('Scan Docker Image') {
          steps {
            script {
              VERSION = infrapool.agentSh(returnStdout: true, script: 'cat VERSION')
            }
            runSecurityScans(infrapool,
              image: "registry.tld/conjur-bitbucket-pipe:${VERSION}",
              buildMode: params.MODE,
              branch: env.BRANCH_NAME)
          }
        }
      }
    }

    stage('Run Tests') {
      steps {
        script {
          infrapool.agentSh './bin/test.sh'
          infrapool.agentStash name: 'coverage', includes: 'coverage.xml'
        }
      }
      post {
        always {
          script {
            unstash 'coverage'
            cobertura(
              coberturaReportFile: "coverage.xml",
              onlyStable: false,
              failNoReports: true,
              failUnhealthy: true,
              failUnstable: false,
              autoUpdateHealth: false,
              autoUpdateStability: false,
              zoomCoverageChart: true,
              maxNumberOfBuilds: 0,
              lineCoverageTargets: '40, 40, 40',
              conditionalCoverageTargets: '80, 80, 80',
              classCoverageTargets: '80, 80, 80',
              fileCoverageTargets: '80, 80, 80',
            )
          }
        }
      }
    }
    
    stage('Release') {
      when {
        expression {
          MODE == "RELEASE"
        }
      }

      steps {
        script {
          release(infrapool, { billOfMaterialsDirectory, assetDirectory ->
            /* Publish release artifacts to all the appropriate locations
               Copy any artifacts to assetDirectory on the infrapool node
               to attach them to the Github release.

               If your assets are on the infrapool node in the target
               directory, use a copy like this:
                  infrapool.agentSh "cp target/* ${assetDirectory}"
               Note That this will fail if there are no assets, add :||
               if you want the release to succeed with no assets.

               If your assets are in target on the main Jenkins agent, use:
                 infrapool.agentPut(from: 'target/', to: assetDirectory)
            */

            // Publish will save docker images to the executing directory
            infrapool.agentSh './bin/publish.sh --edge'
            // Copy the docker images into the assetDirectory for signing in the promote step
            infrapool.agentSh "cp -a docker-image*.tar ${assetDirectory}"
          })
        }
      }
    }
  }
  post {
    always {
      releaseInfraPoolAgent()

      // Resolve ownership issue before running infra post hook
      sh 'git config --global --add safe.directory ${PWD}'
      infraPostHook()
    }
  }
}
