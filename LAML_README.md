# 📜 LAML — Legal/Action Modeling Language

**LAML** (Legal/Action Modeling Language) is a **Domain-Specific Language (DSL)** designed for the **formal representation and computation of legal relations**, such as rights, obligations, permissions, and prohibitions.  
It enables **typed, verifiable reasoning** about legal institutions, contracts, and entities.

---

## 🧩 1. Overview

LAML defines **Persons**, **Things**, and **Services** as typed entities capable of entering legal relations.  
Its purpose is to model legal structures with **computational precision**, allowing a LAML interpreter to verify **logical consistency**, **legal enforceability**, and **institutional outcomes**.

---

## 🧱 2. Basic Types and Subtypes

All variables in LAML must be **explicitly bound** to one of the following **Basic Types** and **Subtypes**.

| Basic Type | Subtypes | Description |
| :--- | :--- | :--- |
| **Person** | `legal`, `physical` | A legal or natural person capable of acting or bearing rights. |
| **Thing** | `movable`, `non-movable` | Tangible or intangible property capable of ownership or transfer. |
| **Service** | `positive`, `omission` | An act performed or a forbearance of an act. |

### Type Binding Syntax
Each variable must be typed explicitly via an **assignment statement**:

```laml
seller(x)  = Person(x, legal)
item(y)    = Thing(y, movable)
service(z) = Service(z, positive)
````

### Wildcard Notation

The underscore `_` may be used in predicates to indicate **any subtype** of a Basic Type.

---

## 🏷️ 3. Statements

Statements define relationships between typed variables.
There are two major kinds of statements: **Facts** and **Acts**.

| Statement Type | Definition                                                 | Variable Requirements                              | Example                                                   |
| :------------- | :--------------------------------------------------------- | :------------------------------------------------- | :-------------------------------------------------------- |
| **Fact**       | Predicate involving **two Persons**.                       | `Person(x,_)`, `Person(y,_)`                       | `murder(x, y) = Person(x, physical), Person(y, physical)` |
| **Act**        | Predicate involving **two Persons and one Thing/Service**. | `Person(x,_)`, `Person(y,_)`, `Thing/Service(z,_)` | `deliver(x, z, y) = seller(x), item(z), buyer(y)`         |

Each statement must use **previously bound** variables only.

---

## ⚙️ 4. Modal (Normative) Operators

Modal operators prefix **Acts** or **Facts** to express their **legal modality** (normative force).

| Operator | Meaning                 | Legal Role                   |
| :------- | :---------------------- | :--------------------------- |
| `claim`  | Enforceable right       | A right held by an entity.   |
| `oblig`  | Obligation or duty      | A mandatory act or service.  |
| `priv`   | Privilege or permission | A permitted act or omission. |
| `forbid` | Prohibition             | A legally prohibited act.    |

### Example:

```laml
oblig(pay(buyer, payment, seller))
claim(deliver(seller, item, buyer))
forbid(murder(a, b))
```

---

## 🧮 5. Rules

Rules define **logical and legal implications** among **Facts**, **Acts**, and **Modal statements**.

### Rule Syntax

```laml
ruleN = <Statement1> <operator> <Statement2>
```

### Allowed Operators

| Token     | Meaning                       |
| :-------- | :---------------------------- |
| `and`     | Logical conjunction           |
| `or`      | Logical disjunction           |
| `xor`     | Exclusive disjunction         |
| `not`     | Negation                      |
| `implies` | Logical implication (if–then) |

### ❗ Rule Constraints

1. **Rules are atomic.**

   * A rule may not contain or reference another rule.
   * Invalid: `rule3 = rule1 and rule2`

2. **Rules operate only on Facts, Acts, or Modal statements.**

3. **All variables** in a rule must be previously **typed** and declared.

### Example:

```laml
rule1 = deliver(x, z, y) implies claim(pay(y, p, x))
rule2 = pay(y, p, x) implies claim(deliver(x, z, y))
rule3 = oblig(pay(y, p, x))
rule4 = forbid(murder(a, b))
```

---

## 🏛️ 6. Institutions

An **Institution** is a parameterized legal framework (template) that encapsulates:

* Typed variable definitions
* Facts and Acts
* Rules that describe their relationships

Institutions model contracts, laws, or organizational frameworks.

### 6.1. Institution Definition Syntax

```
institution_name(param₁, param₂, ..., paramₙ) = institution(param₁, param₂, ..., paramₙ) {
    ... body ...
}
```

**All parameters** used within the body must appear in the header.

### 6.2. Body Structure

The body of an institution must include **only**:

* Typed variable declarations
* Facts and Acts
* Rules (not composed from other rules)

### 6.3. Typing Constraint

Institutions are **untyped** (they are not Things).
They serve as **blueprints** and cannot appear as arguments in Acts or Facts.

---

## 💾 7. Execution Protocol

LAML defines a minimal computational interface for validating and extracting the results of institutional definitions.

### 7.1. `valid()`

**Action:**
Computes the **logical satisfiability** of all Facts, Acts, and Rules within the institution.
If all are consistent, returns `Satisfiable`; otherwise, `Unsatisfiable`.

```laml
sale_contract.valid() → Satisfiable
```

### 7.2. `directObject()`

**Precondition:**
May only be called if `valid()` returned `Satisfiable`.

**Action:**
Extracts all **enforceable claims** from the institution's rules, including:

1. **Explicit claims**: All `claim(...)` statements in rules
2. **Correlative claims**: Derived from `oblig(...)` statements (Hohfeldian transformation)
   - `oblig(pay(x, p, y))` → `claim(pay(x, p, y))`
3. **Negation claims**: Derived from `forbid(...)` statements
   - `forbid(murder(a, b))` → `claim(not_murder(a, b))`

**Return Type:**
A `Thing(movable)` composed of all enforceable claims.  
Claims are movable as they can be transferred or assigned.

```laml
sale_contract.directObject()
→ Thing({ claim(pay(...)), claim(deliver(...)) }, movable)
```

**Note:** `directObject()` recursively traverses all rules in the institution to extract claims from nested logical expressions (`and`, `or`, `implies`, etc.).

---

## 🧾 8. Example: Sale Contract Institution

```laml
sale_contract(x, y, z, p) = institution(x, y, z, p) {

    # Typed roles
    seller(x)  = Person(x, legal)
    buyer(y)   = Person(y, legal)
    item(z)    = Thing(z, movable)
    payment(p) = Service(p, positive)

    # Acts
    deliver(x, z, y) = seller(x), item(z), buyer(y)
    pay(y, p, x)     = buyer(y), payment(p), seller(x)

    # Facts
    murder(a, b) = Person(a, physical), Person(b, physical)

    # Independent rules (no rule composition)
    rule1 = deliver(x, z, y) implies claim(pay(y, p, x))
    rule2 = pay(y, p, x) implies claim(deliver(x, z, y))
    rule3 = oblig(pay(y, p, x))
    rule4 = forbid(murder(a, b))
}
```

### Execution

```laml
contract1 :- sale_contract(Alice_Corp, Bob_Ltd, car_001, wire_payment_001)

contract1.valid()        → Satisfiable
contract1.directObject() → Thing({
                                claim(pay(Bob_Ltd, wire_payment_001, Alice_Corp)),
                                claim(deliver(Alice_Corp, car_001, Bob_Ltd))
                             }, movable)
```

---

## 🔧 9. Compiler Behavior and File Generation

### 9.1. Multiple `.valid()` Calls

The LAML compiler processes **all** `.valid()` calls in the order they appear in your file. Each execution:

- Creates a separate clause model
- Generates unique output files
- Calls the SAT solver independently
- Produces separate solution sets

**Example:**
```laml
# Component 1
lease_component.valid()        # → Execution #1

# Component 2  
generation_component.valid()   # → Execution #2

# Final composite
composite_lease.valid()        # → Execution #3
```

The compiler processes all three executions sequentially, generating separate results for each.

### 9.2. Generated Files

For each `.valid()` call on instance `{instance_name}`, the compiler generates:

| File Pattern | Purpose | Persistence |
|:------------|:--------|:------------|
| `witness_{instance_name}.json` | Input to SAT solver | Temporary (deleted after execution) |
| `laml_results_{instance_name}.json` | **Final results** (solutions, satisfiability) | **Persistent** |
| `solver_{instance_name}_{pid}.bin` | Solver binary output | Temporary (deleted after parsing) |

**Note:** File names are **automatically generated** based on instance names. You cannot control file names directly.

### 9.3. Identifying the "Main" Contract

There is no explicit "main" contract designation. Typically:

- **The last execution** in your file represents the final composite contract
- **Component executions** validate base laws/institutions in isolation
- **Final execution** validates the complete composed legal framework

The `laml_results_{final_instance}.json` file contains the authoritative solution space for your complete contract.

---

## 🧩 10. Composition Semantics and Workflow

### 10.1. Component vs Final Contract Analysis

When composing multiple institutions:

**Components** (e.g., `lease_component.valid()`):
- Validate the component institution in isolation
- Generate `laml_results_{component}.json`
- Verify component logic before composition
- Extract claims via `directObject()` for conceptual reference

**Final Contract** (e.g., `composite_lease.valid()`):
- Validates the complete composite with all rules and constraints
- Generates `laml_results_{final_contract}.json`
- Contains the authoritative solution space
- **This is the "main" contract result**

### 10.2. `directObject()` in Composition

The `directObject()` method extracts claims conceptually — it does not directly compose institutions. Instead:

1. **Extract claims** from base law components:
   ```laml
   lease_claims = lease_component.directObject()
   generation_claims = generation_component.directObject()
   ```

2. **Create composite institution** that re-declares necessary acts/rules:
   ```laml
   composite_lease(...) = institution(...) {
       # Re-declare acts from components
       grant_possession(...) = ...
       pay_rent(...) = ...
       
       # Re-declare rules from components
       rule_rent_obligation = ...
       
       # Add composite-specific rules
       rule_composite_enhancement = ...
   }
   ```

3. **Validate the composite** to get the complete solution:
   ```laml
   final_lease :- composite_lease(...)
   final_lease.valid()  # → laml_results_final_lease.json (MAIN RESULT)
   ```

### 10.3. Recommended Workflow

**Pattern: Component → Extraction → Composition**

```laml
# Step 1: Import base laws
import "../laws/lease_law.laml"
import "../laws/generation_law.laml"

# Step 2: Instantiate components
lease_component :- lease_law(Landlord, Tenant, Property, Rent)
generation_component :- generation_law(Provider, System, Consumer)

# Step 3: Extract claims (conceptual reference)
lease_claims = lease_component.directObject()
generation_claims = generation_component.directObject()

# Step 4: Validate components separately
lease_component.valid()        # → laml_results_lease_component.json
generation_component.valid()   # → laml_results_generation_component.json

# Step 5: Create composite institution
composite_solar_lease(...) = institution(...) {
    # Re-declare acts from components
    # Re-declare rules from components  
    # Add composite-specific rules
}

# Step 6: Validate final composite (MAIN CONTRACT)
final_contract :- composite_solar_lease(...)
final_contract.valid()  # → laml_results_final_contract.json (AUTHORITATIVE)
```

### 10.4. Analysis Strategy

1. **Validate components first**: Check `laml_results_{component}.json` files to verify component correctness
2. **Analyze final contract**: The `laml_results_{final_contract}.json` file contains the authoritative solution
3. **Store component results**: Keep component results for debugging and validation
4. **Use final contract as source of truth**: The final composite's `.valid()` result represents the complete legal framework

**Key Principle:** Component results validate logic in isolation; final contract results represent the complete composed legal system.

---

## 🚫 11. Invalid Constructs

| Invalid Example                                | Reason                                                    |
| :--------------------------------------------- | :-------------------------------------------------------- |
| `rule3 = rule1 and rule2`                      | Rules cannot operate on other rules.                      |
| `deliver(x, y, z)` without prior type bindings | All variables must be explicitly bound.                   |
| `institution` used as a predicate argument     | Institutions are untyped and cannot appear in Facts/Acts. |
| `directObject()` before `valid()`              | Must be called only if institution is satisfiable.        |

---

## 🧠 12. Conceptual Summary

* **LAML** encodes *legal semantics* as *computable logic*.
* It is **strictly typed**, **rule-atomic**, and **institutionally scoped**.
* Each valid institution can yield a **legally transferable object** — the **directObject** — representing enforceable claims (including explicit claims, correlative claims from obligations, and negation claims from prohibitions).
* **Composition** allows building complex legal frameworks from reusable base institutions, with components validated separately and final composites representing the complete legal system.
* The compiler processes multiple executions sequentially, generating separate solution sets for each `.valid()` call, with the final execution representing the authoritative contract result.
* This provides a foundation for **computable legal systems**, **smart contracts**, and **institutional simulation**.

---

**Version:** 1.0
**Specification Maintainer:** LAML Working Group
**Status:** Draft (Computable Legal Semantics)

```
---

Would you like me to extend this README with a **formal grammar (BNF-style)** section next, so the syntax can be parsed automatically by a compiler/interpreter?
```
