# Deliverability-Gated Market Clearing

**Status:** PROMOTED v0.1

**Composition:** CDBL + MCPR

Replaces nominal offered quantity with deadline- and network-constrained deployable quantity before uniform-price market clearing.

## Benchmark

```json
{
  "nominal_market": {
    "status": "CLEARED",
    "served_quantity": 70.0,
    "unserved_quantity": 0.0,
    "clearing_price": 10.0,
    "dispatch": [
      {
        "name": "cheap",
        "quantity": 70.0
      },
      {
        "name": "expensive",
        "quantity": 0.0
      }
    ]
  },
  "deployable_market": {
    "status": "CLEARED",
    "served_quantity": 70.0,
    "unserved_quantity": 0.0,
    "clearing_price": 30.0,
    "dispatch": [
      {
        "name": "cheap",
        "quantity": 20.0
      },
      {
        "name": "expensive",
        "quantity": 50.0
      }
    ]
  },
  "quantities": [
    {
      "name": "cheap",
      "nominal_quantity": 100.0,
      "deployable_quantity": 20.0,
      "conversion_ratio": 0.2,
      "price": 10
    },
    {
      "name": "expensive",
      "nominal_quantity": 80.0,
      "deployable_quantity": 80.0,
      "conversion_ratio": 1.0,
      "price": 30
    }
  ],
  "hidden_shortfall": 0.0,
  "price_uplift": 20.0,
  "status": "NOMINAL_SUPPLY_OVERSTATES_DELIVERABILITY"
}
```

## Claim boundary

CDBL quantities are physical/operational deployability under the declared network. DGMC does not infer strategic availability, forced outages, or offer-price changes unless explicitly represented upstream.
