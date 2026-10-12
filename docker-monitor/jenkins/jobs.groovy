def repoUrl = System.getenv('GIT_REPO_URL') ?: 'https://github.com/manoVaturi/devops-assignment.git'

def fromRepo = { String jenkinsfile ->
    return {
        cpsScm {
            scm {
                git {
                    remote {
                        url(repoUrl)
                        credentials('github-token')
                    }
                    branches('main')
                }
            }
            scriptPath(jenkinsfile)
        }
    }
}

// set by the integration job
def targetHash = {
    stringParam('TARGET_HASH', '', 'Commit to build (set by the integration job); empty = branch head')
}

pipelineJob('docker-monitor-pipeline') {
    description('CI/CD Pipeline for Docker Monitor App.')
    parameters(targetHash)
    definition(fromRepo('docker-monitor/jenkins/Jenkinsfile.monitor'))
}

pipelineJob('docker-monitor-nginx-pipeline') {
    description('Builds the Nginx reverse-proxy image and pushes it to Docker Hub.')
    parameters(targetHash)
    definition(fromRepo('docker-monitor/jenkins/Jenkinsfile.nginx'))
}

pipelineJob('docker-monitor-integration-pipeline') {
    description('Integration pipeline: builds both images, runs them and verifies the proxy.')
    definition(fromRepo('docker-monitor/jenkins/Jenkinsfile.integration'))
}

// seed job runs this file on every push, then the integration pipeline starts
queue('docker-monitor-integration-pipeline')
