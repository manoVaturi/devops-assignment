# Docker Monitor

A Flask app that lists the running Docker containers, an Nginx proxy in front of it that adds the
client IP as an `X-Source-IP` header, and three Jenkins pipelines that build both images, push
them to Docker Hub and test them together. Jenkins runs on one EC2 instance.

| Assignment item | Where |
| --- | --- |
| Groovy (Job DSL) file that creates the jobs | `jenkins/jobs.groovy`, run by the `seed` job |
| Job 1: build the Flask app image, push to Docker Hub | `docker-monitor-pipeline`, `jenkins/Jenkinsfile.monitor`, app in `monitor/` |
| Job 2: Nginx image with `proxy_pass` and the source IP header, push to Docker Hub | `docker-monitor-nginx-pipeline`, `jenkins/Jenkinsfile.nginx`, config in `nginx/` |
| Job 3: run both containers, Nginx exposed on the Jenkins machine only, send a request | `docker-monitor-integration-pipeline`, `jenkins/Jenkinsfile.integration`, `docker-compose.yaml` |

Job 3 is the entry point: it runs jobs 1 and 2 for one commit, then tests the images they pushed.
A push to `main` that changes `docker-monitor/` triggers `seed`, which recreates the jobs and
starts job 3. `jobs.groovy` also creates `weatherapp-image-pipeline` for the second project.

```
push to main -> seed -> integration pipeline
                          |-> docker-monitor-pipeline        lint, SAST, tests, build, scan, push
                          |-> docker-monitor-nginx-pipeline  build, config test, scan, push
                          '-> pull both images, compose up, verify, tag latest

127.0.0.1:8090 -> nginx (adds X-Source-IP) -> Flask app -> docker-socket-proxy -> docker.sock
```

Images: `<dockerhub-user>/docker-monitor-app` and `<dockerhub-user>/docker-monitor-nginx`, tagged
with the short commit SHA. `latest` moves only after job 3 passes.

## What job 3 checks

The checks run from throwaway containers on the compose network. Only the last one uses the host
network, because `127.0.0.1` there is the instance itself, where nginx is published.

1. A request to nginx returns 200.
2. `/containers` lists the nginx container, so the app reaches Docker.
3. Forged `X-Source-IP` and `X-Forwarded-For` headers are ignored: the app log shows the real source IP.
4. Nginx is published on `127.0.0.1:8090` only: other addresses of the instance refuse the port.

If all pass, both images are tagged `latest` and the Deploy stage runs the same stack as project
`monitor-prod` on the Jenkins machine, reachable at https://monitor.manovaturi.com.

## AWS

Terraform (state in S3) creates one EC2 instance from a golden AMI (Amazon Linux 2023 + Docker +
Compose), an ALB with ACM certificates, Route 53 records for `jenkins.manovaturi.com` and
`monitor.manovaturi.com`, and the Secrets Manager secrets.

- Jenkins is configured entirely by Configuration as Code, no setup wizard.
- Credentials (admin, Docker Hub, GitHub) come from Secrets Manager through the instance role,
  there is no `.env` with secrets.
- At boot the instance waits for the secrets, clones the repo and starts Jenkins.
- Admin access is through SSM, no SSH and no open inbound ports. The ALB sends
  `monitor.manovaturi.com` to the app and everything else to Jenkins.

## Notes

- Behind the ALB the peer nginx sees is the load balancer, so nginx takes the client IP from the
  last `X-Forwarded-For` entry (the one the ALB adds), and only trusts that header from the VPC.
- The app never touches the Docker socket: it asks `docker-socket-proxy`, which only allows `GET /containers`.
- Job 3 tests the images pulled from Docker Hub, not the local cache.
- Trivy only reports, a new CVE in a base image does not fail the build.
- Everything is pinned: base images, tools, Python packages, Jenkins and its plugins.
- `docker.sock` is root-equivalent on the host, so the instance is treated as a build box.
- `useScriptSecurity: false` lets the seed job run `jobs.groovy` without approval. I'd leave it on in production.

## Layout

```
monitor/                    Flask app, tests, Dockerfile
nginx/                      Nginx image
jenkins/                    jobs.groovy and the three Jenkinsfiles
infrastructure/             Jenkins: Dockerfile, plugins.txt, agent image, casc/jenkins.yaml, compose
infrastructure/terraform/   AWS: instance, ALB, certificates, DNS, secrets
docker-compose.yaml         the app stack (job 3)
```
