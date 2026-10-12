# DevOps home assignment

Two projects, each in its own folder with its own README.

| Part | Folder | Live |
| --- | --- | --- |
| Jenkins Job DSL: build a Flask app and an Nginx proxy, push both to Docker Hub, run and verify them | [`docker-monitor/`](docker-monitor/) | [Jenkins](https://jenkins.manovaturi.com), [Monitor](https://monitor.manovaturi.com) |
| Weather app on Kubernetes (EKS) with RabbitMQ, scaled by KEDA | [`weatherapp-keda/`](weatherapp-keda/) | [Weather app](http://weatherapp.manovaturi.com) |

## Assignment items

| Item | Where |
| --- | --- |
| Groovy file that creates the Jenkins jobs (Job DSL plugin) | `docker-monitor/jenkins/jobs.groovy`, run by the `seed` job from `infrastructure/casc/jenkins.yaml` |
| Job 1: pull from GitHub, build the Flask app (lists running containers from the local Docker engine), push to Docker Hub | `docker-monitor/jenkins/Jenkinsfile.monitor`, app in `docker-monitor/monitor/` |
| Job 2: Nginx image with `proxy_pass` to the app and the source IP injected as a request header, push to Docker Hub | `docker-monitor/jenkins/Jenkinsfile.nginx`, config in `docker-monitor/nginx/` |
| Job 3: run both containers, Nginx exposed on the Jenkins machine only, send a request and verify it | `docker-monitor/jenkins/Jenkinsfile.integration`, `docker-monitor/docker-compose.yaml` |
| K8s cluster with my weather app, a 3rd party queue, KEDA scaling the pods by user requests | `weatherapp-keda/` (Terraform EKS, RabbitMQ, KEDA ScaledObjects) |

## Stack

Jenkins (Job DSL, Configuration as Code), Docker, Docker Compose, Flask, Nginx, Trivy,
Terraform, AWS (EC2, ALB, ACM, Route 53, Secrets Manager, EKS), Kubernetes, kustomize,
RabbitMQ, KEDA, Helm.

## Layout

```text
docker-monitor/
  monitor/          Flask app that lists the running containers
  nginx/            reverse proxy, adds X-Source-IP
  jenkins/          jobs.groovy + the three Jenkinsfiles
  infrastructure/   Jenkins image, plugins, CasC, Terraform for EC2
weatherapp-keda/
  weather-app/      Flask web + queue worker, tests
  k8s/              RabbitMQ, app, worker, KEDA ScaledObject (kustomize)
  infrastructure/   Terraform: VPC + EKS
  dns/              Terraform: Route 53 record
```
