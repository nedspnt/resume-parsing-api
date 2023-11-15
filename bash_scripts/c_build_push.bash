docker build -t resume-parsing-image:latest .
docker tag resume-parsing-image:latest asia-east1-docker.pkg.dev/data-analytics-gcp/resume-parsing-api/resume-parsing-api-image:latest
docker push asia-east1-docker.pkg.dev/data-analytics-gcp/resume-parsing-api/resume-parsing-api-image