# Challenge — Kubernetes

## Build It Yourself

Deploy a complete microservices application on Minikube using Terraform.

### Requirements

1. Create a namespace called `challenge-app`

2. Create a ConfigMap with:
   - `DATABASE_URL=postgres://localhost:5432/mydb`
   - `REDIS_URL=redis://localhost:6379`
   - `LOG_LEVEL=info`

3. Create a Secret with:
   - `DB_PASSWORD` (use `random_password` to generate)
   - `API_KEY` (use `random_password` to generate)

4. Deploy 3 services using `for_each`:
   ```
   frontend: nginx:alpine, 2 replicas, NodePort 30200
   api:      httpd:alpine, 3 replicas, NodePort 30201
   worker:   nginx:alpine, 1 replica,  ClusterIP (no NodePort)
   ```

5. Each deployment should:
   - Mount the ConfigMap as environment variables
   - Mount the Secret as environment variables
   - Have resource limits (cpu: 100m, memory: 64Mi)
   - Have a liveness probe on port 80

6. Create Services:
   - `frontend` and `api` as NodePort
   - `worker` as ClusterIP

7. Create a ServiceAccount `app-sa` with a Role that can read pods and configmaps

### Outputs
- Namespace name
- Map of service name → service type
- kubectl command to check all resources

## Verify
```bash
minikube start --driver=docker
terraform init
terraform apply
kubectl get all -n challenge-app
kubectl get configmap -n challenge-app
kubectl get secrets -n challenge-app
minikube service frontend -n challenge-app --url
terraform destroy
```
