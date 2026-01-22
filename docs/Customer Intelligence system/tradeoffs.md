# System Trade-offs

This document captures intentional trade-offs made in system design.

---

## Batch vs Real-Time

**Chosen**
- Batch-first

**Pros**
- Stability
- Reproducibility
- Lower operational cost

**Cons**
- Limited immediacy
- Not suitable for in-session use cases

---

## Simplicity vs Accuracy

**Chosen**
- Interpretable, robust models over maximum complexity

**Pros**
- Easier governance
- Better trust
- Faster iteration

**Cons**
- Potentially lower ceiling performance

---

## Generality vs Specialization

**Chosen**
- General-purpose customer intelligence

**Pros**
- Reusable across teams
- Lower maintenance overhead

**Cons**
- Less optimized for niche use cases

---

## Synthetic Data Compatibility

**Chosen**
- Privacy-first, low-data operation

**Pros**SS
- Compliance-friendly
- Portable
- Safer experimentation

**Cons**
- Possible realism gap
- Requires careful validation

---

## Centralization vs Flexibility

**Chosen**
- Centralized feature and model definitions

**Pros**
- Consistency
- Reduced duplication

**Cons**
- Slower local experimentation without coordination