# Weather app on Kubernetes with KEDA

My weather app running on a Kubernetes cluster, with a queue in the middle and KEDA scaling the
pods up and down based on user requests.

## How it works

The web pods don't call the weather API directly. Every forecast request is published to a
RabbitMQ queue and the web pod waits for the answer. Worker pods take requests from the queue,
call WeatherAPI and send the result back (`reply_to` + `correlation_id`).

KEDA watches the queue length and scales the workers: 0 when nobody is using the app, one
worker for every 3 waiting requests, up to 5. Workers go back to 0 about 30 seconds after the
queue is empty.

```
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
- Flask + gunicorn, one Docker image for both web and worker (`ormano/weatherapp`)
- Route 53 record for weatherapp.manovaturi.com

The same manifests also run on a local kind cluster.

## Layout

```
weather-app/      Flask web app, queue client and worker, Dockerfile
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
- The worker Deployment has no `replicas` field, so `kubectl apply` doesn't fight with KEDA.

## What I'd change for production

- RabbitMQ as a cluster with persistent storage, or Amazon MQ
- Autoscaling for the web tier too, and Karpenter for the nodes
- HTTPS through an ALB with an ACM certificate
- Secrets from AWS Secrets Manager
- A CI/CD pipeline that builds the image and updates the tag
