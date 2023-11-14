kubectl delete deployment resume-parsing-api-deployment
kubectl create deployment resume-parsing-api-deployment \
    --image=asia-east1-docker.pkg.dev/data-analytics-gcp/resume-parsing-api/resume-parsing-api-image:latest