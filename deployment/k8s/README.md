# How to deploy using kubectl

You need kubectl binary: [Kubectl Installation](https://kubernetes.io/docs/tasks/tools/install-kubectl/)

Specify your kubeconfig location.

```bash
export KUBECONFIG=<kubeconfig file yaml location>
```

Set your deployment namespace

```bash
kubectl config set-context --current --namespace <your namespace>
```

Apply the manifests

```bash
kubectl apply -f .
```

When you update the manifests, just reapply them to deploy using the same command
