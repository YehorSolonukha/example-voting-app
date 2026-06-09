# Wdrożenie stosu monitoringu (Prometheus + Grafana) na klastrze AKS

## Wymagania wstępne
- Działający klaster AKS (wdrożony przez Terraform)
- Skonfigurowany `kubectl` połączony z klastrem
- Zainstalowany Helm v3+

## Krok 1: Dodanie repozytorium Helm

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

## Krok 2: Utworzenie przestrzeni nazw

```bash
kubectl create namespace monitoring
```

## Krok 3: Wdrożenie stosu monitoringu

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values values.yaml
```

## Krok 4: Weryfikacja wdrożenia

```bash
# Sprawdzenie, czy wszystkie Pody w przestrzeni monitoringu działają
kubectl get pods -n monitoring

# Pobranie zewnętrznego adresu IP Grafany
kubectl get svc -n monitoring prometheus-grafana
```

## Krok 5: Dostęp do Grafany

1. Skopiuj `EXTERNAL-IP` z komendy powyżej
2. Otwórz w przeglądarce: `http://<EXTERNAL-IP>`
3. Zaloguj się:
   - **Login:** `admin`
   - **Hasło:** `prom-operator`
4. Przejdź do: **Dashboards → Browse → Kubernetes / Compute Resources / Namespace (Pods)**
5. Wybierz namespace `default` — zobaczysz metryki CPU i RAM swoich mikroserwisów

## Alternatywny dostęp (port-forward, bez LoadBalancer)

Jeśli nie chcesz używać publicznego IP:

```bash
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
```

Następnie otwórz: `http://localhost:3000`
