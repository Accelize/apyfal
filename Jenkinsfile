pipeline {
    agent {
        label 'jenkins-rtda-agent'
    }
    stages {
        stage('Build') {
            steps {
                sh '''
                    # Python environment (RHEL 7 Python 3.6)
                    source /opt/rh/rh-python36/enable
                    python -m venv venv
                    source venv/bin/activate
                    python -m pip install --upgrade pip
                    python -m pip install --upgrade setuptools wheel pytest coverage pytest-cov codecov --upgrade-strategy eager

                    # Installs all package dependencies
                    python -m pip install -e .[all] --upgrade-strategy eager

                    # Installs pre-releases of pycosio
                    python -m pip install pycosio[all] --pre --upgrade-strategy eager
                '''
            }
        }
        stage('Test') {
            steps {
                withCredentials([file(credentialsId: 'apyfal_config_file', variable: 'APYFAL_CONFIG_FILE')]) {
                    sh '''
                        # Enables environment
                        source /opt/rh/rh-python36/enable
                        source venv/bin/activate

                        # Runs tests
                        py.test -v --cov=apyfal --cov-report=term-missing
                    '''
                }
            }
        }
        stage('CoverageReport') {
            steps {
                withCredentials([string(credentialsId: 'apyfal_codecov_token', variable: 'TOKEN')]) {
                    sh '''
                        # Enables environment
                        source /opt/rh/rh-python36/enable
                        source venv/bin/activate

                        # Sends coverage to codecov.io
                        codecov --token=$TOKEN
                    '''
                }
            }
        }
    }
}
