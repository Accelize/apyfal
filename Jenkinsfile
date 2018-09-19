pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                /* Python environment */
                python -m pip install --upgrade setuptools pip wheel pytest coverage pytest-cov codecov

                /* Installs all package dependencies */
                python -m pip install -e .[all]

                /* Installs pre-releases of pycosio */
                python -m pip install pycosio[all] --pre
            }
        }
        stage('Test') {
            steps {
                py.test -v --cov=apyfal --cov-report=term-missing
            }
        }
        stage('CoverageReport') {
            when {
              expression {
                currentBuild.result == 'SUCCESS'
              }
            }
            steps {
                codecov
            }
        }
    }
}
