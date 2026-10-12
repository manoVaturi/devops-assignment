# Weather app on Kubernetes with KEDA

My weather app running on a Kubernetes cluster, with a queue in the middle and KEDA scaling the
pods up and down based on user requests.

## How it works

The web pods don't call the weather API directly. Every forecast request is published to a
RabbitMQ queue and the web pod waits for the answer. Worker pods take requests from the queue,
call WeatherAPI and send the result back (`reply_to` + `correlation_id`).

KEDA scales both tiers:

- workers on the queue length: 0 when nobody is using the app, one worker for every 3 waiting
  requests, up to 5. They go back to 0 about 30 seconds after the queue is empty.
- web pods on CPU (metrics-server): 2 to 4.

Each web thread keeps one RabbitMQ connection and reuses it, with its own reply queue. If the
broker drops an idle connection, the next request reconnects and retries once.

```text
browser -> web (Flask) -> RabbitMQ queue -> worker -> WeatherAPI
                               ^
                               |
                             KEDA  (queue length -> number of workers)
```

## Stack

- AWS EKS 1.35, VPC and cluster built with Terraform (state in S3)
- RabbitMQ 4.3 as the queue
- KEDA 2.21 (installed with Helm) with a RabbitMQ trigger
- Kubernetes manifests with kustomize
- Flask + gunicorn, one Docker image for both web and worker (`ormano/weatherapp`), unit tests with pytest
- Route 53 record for weatherapp.manovaturi.com

The same manifests also run on a local kind cluster (with metrics-server installed).

Secrets are not in the repo. The `weather` namespace needs three of them:
`weather-api-secret` (WeatherAPI key), `rabbitmq-credentials` (user, password and AMQP URL, used
by the app and by KEDA) and `rabbitmq-definitions` (`definitions.json` that RabbitMQ loads at
startup to create the user and the queue).

## Layout

```text
weather-app/      Flask web app, queue client and worker, tests, Dockerfile
k8s/              RabbitMQ, web app, worker, KEDA TriggerAuthentication + ScaledObject
infrastructure/   Terraform: VPC, EKS cluster, node group, add-ons
dns/              Terraform: Route 53 record for the load balancer
```

## Things I ran into

- With gunicorn's default sync workers only 3 requests could wait on the queue at the same
  time, so KEDA never started more than one worker. It now runs 3 processes x 20 threads.
- KEDA couldn't scale up from zero because the queue didn't exist until a worker created it.
  RabbitMQ now creates the queue at startup from a definitions file.
- The AWS load balancer wasn't created because two security groups had the cluster tag.
  Removing the tag from the node security group fixed it.
- The Deployments have no `replicas` field, so `kubectl apply` doesn't fight with KEDA.
- The web pod used to open a new RabbitMQ connection for every request. Under the load test that
  was a lot of connection churn, so each thread now keeps its connection.

## Trade-offs

- Scaling workers to 0 means the first request after an idle period waits for a worker pod to
  start (a few seconds, the web pod waits up to 45). `minReplicaCount: 1` removes that for the
  cost of one idle pod.
- The Kubernetes API endpoint is public, limited by `api_allowed_cidrs` in Terraform (open by
  default so the demo works from any network).

## What I'd change for production

- RabbitMQ as a cluster with persistent storage, or Amazon MQ
- Karpenter for the nodes
- HTTPS through an ALB with an ACM certificate
- Secrets from AWS Secrets Manager
- GitOps (Argo CD) to roll out the new image tag instead of editing `kustomization.yaml`
