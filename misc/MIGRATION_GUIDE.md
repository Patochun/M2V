# Guide de Migration - Utilisation du Contexte d'Animation

## Vue d'ensemble

Le système d'état global a été remplacé par un système basé sur `AnimationContext`. Ce guide aide les développeurs à comprendre et utiliser le nouveau système.

## Concepts fondamentaux

### AnimationContext
Conteneur immutable pour l'état d'animation :
```python
from m2v.engine.context import AnimationContext

ctx = AnimationContext()
ctx.fps = 30
ctx.tracks = track_list
ctx.last_note_time_off = 100.5
# ... autres propriétés
```

### Gestionnaire de contexte
Crée et gère un contexte pour une opération :
```python
from m2v.engine.context import with_animation_context

with with_animation_context() as ctx:
    ctx.fps = scene.render.fps
    # ctx disponible dans tout le bloc
```

### Rétrocompatibilité (Proxy)
Le code existant continue de fonctionner :
```python
from m2v.engine.globals import glb
glb.fps = 30  # Délègue au contexte courant via proxy
```

## Modèles de migration

### Pattern 1 : Entrée (très recommandé)

**Avant :**
```python
def execute_animation(anim_type, track_mask):
    glb.fps = scene.render.fps
    glb.tracks = track_list
    animate(anim_type, track_mask)
```

**Après :**
```python
def execute_animation(anim_type, track_mask):
    with with_animation_context() as ctx:
        ctx.fps = scene.render.fps
        ctx.tracks = track_list
        animate(anim_type, track_mask)
        # ctx est automatiquement disponible pour animate()
```

### Pattern 2 : Fonction réceptrice

**Avant :**
```python
def process_tracks():
    for track in glb.tracks:
        # traiter track
```

**Après :**
```python
def process_tracks(ctx: AnimationContext):
    for track in ctx.tracks:
        # traiter track

# Appelé depuis :
with with_animation_context() as ctx:
    process_tracks(ctx)
```

### Pattern 3 : Plusieurs niveaux

**Avant :**
```python
def level1():
    glb.fps = 30
    level2()

def level2():
    level3()

def level3():
    print(glb.fps)
```

**Après :**
```python
def level1(ctx: AnimationContext):
    ctx.fps = 30
    level2(ctx)

def level2(ctx: AnimationContext):
    level3(ctx)

def level3(ctx: AnimationContext):
    print(ctx.fps)

# Utilisé depuis :
with with_animation_context() as ctx:
    level1(ctx)
```

## Exemples concrets

### Exemple 1 : Initialisation MIDI

**Ancien code :**
```python
# m2v/ext/ops.py
def execute(self, context):
    init_log(paths["log"])
    init_collections()
    glb.fps = scene.render.fps
    midi_file, _, glb.tracks = read_midi_file(paths["midi"])
    animate(m2b.animation_type, m2b.track_mask)
```

**Nouveau code :**
```python
# m2v/ext/ops.py
def execute(self, context):
    with with_animation_context() as ctx:
        set_animation_context(ctx)  # Pour rétrocompatibilité
        
        init_log(paths["log"], ctx)
        init_collections(ctx)
        ctx.fps = scene.render.fps
        midi_file, _, ctx.tracks = read_midi_file(paths["midi"])
        
        animate(m2b.animation_type, m2b.track_mask)
        # ctx est automatiquement accessible via proxy
```

### Exemple 2 : Utilitaires avec contexte

**Ancien code :**
```python
# m2v/engine/utils/stuff.py
def w_log(to_log):
    print(to_log)
    glb.f_log.write(to_log + "\n")

def parse_range_from_tracks(range_str):
    tracks = glb.tracks
    # ...
```

**Nouveau code :**
```python
# m2v/engine/utils/stuff.py
def w_log(to_log: str, ctx: AnimationContext) -> None:
    print(to_log)
    if ctx.f_log is not None:
        ctx.f_log.write(to_log + "\n")

def parse_range_from_tracks(range_str: str, ctx: AnimationContext) -> tuple:
    tracks = ctx.tracks
    # ...
    w_log(f"Track filter used = {range_str}", ctx)
    # ...
```

## Recommandations par type de fichier

### Fichiers d'entrée (ops.py, main)
✅ **OBLIGATOIRE** : Utiliser `with_animation_context()`
```python
def execute(self, context):
    with with_animation_context() as ctx:
        set_animation_context(ctx)
        # ... votre code
```

### Fichiers utilitaires (utils/)
✅ **FORTEMENT RECOMMANDÉ** : Accepter `ctx` en paramètre
```python
def helper_function(ctx: AnimationContext) -> None:
    # Utiliser ctx au lieu de glb
```

### Fichiers d'animation (animations/)
✅ **RECOMMANDÉ** : Accepter `ctx` en paramètre
```python
def fountain_animation(ctx: AnimationContext, track_mask: str) -> None:
    # Utiliser ctx au lieu de glb
```

✅ **ACCEPTABLE** : Continuer avec proxy pour migration progressive
```python
def fountain_animation(track_mask: str) -> None:
    from m2v.engine.globals import glb
    # glb fonctionne via proxy (rétrocompatible)
    for track in glb.tracks:
        # ...
```

## Checklist de migration

Pour migrer une fonction :

- [ ] Ajouter `ctx: AnimationContext` à la signature
- [ ] Remplacer `glb.attribute` par `ctx.attribute`
- [ ] Passer `ctx` aux fonctions appelées
- [ ] Tester le code (manuellement ou unitaires)
- [ ] Mettre à jour la documentation
- [ ] Passer en revue le code

Exemple complet :
```python
def process_tracks(ctx: AnimationContext) -> int:
    """Process all tracks in animation context."""
    count = 0
    for track in ctx.tracks:
        # traiter track
        count += 1
    
    # Appel à une fonction qui utilise aussi ctx
    w_log(f"Processed {count} tracks", ctx)
    return count
```

## Dépannage

### Erreur : "Animation context not initialized"
**Cause** : `get_animation_context()` appelé hors de `with_animation_context()`
```python
# INCORRECT
ctx = get_animation_context()

# CORRECT
with with_animation_context() as ctx:
    # utiliser ctx
```

### Erreur : "glb.attribute is None"
**Cause** : Le contexte n'a pas été initialisé avant d'accéder à l'attribut
```python
# INCORRECT
ctx.fps = None
print(ctx.fps)  # None

# CORRECT
ctx.fps = 30
print(ctx.fps)  # 30
```

### Le proxy glb ne fonctionne pas
**Vérifier** : `set_animation_context(ctx)` a été appelé après `with_animation_context()`
```python
# INCORRECT
with with_animation_context() as ctx:
    # Le proxy glb n'est pas encore défini
    glb.fps = 30

# CORRECT
with with_animation_context() as ctx:
    set_animation_context(ctx)
    glb.fps = 30  # Fonctionne via proxy
```

## Bonnes pratiques

1. **Toujours initier en haut niveau**
   ```python
   # Dans le point d'entrée (operator ou function principale)
   with with_animation_context() as ctx:
       # Passer ctx en cascade
   ```

2. **Utiliser les types pour la clarté**
   ```python
   from m2v.engine.context import AnimationContext
   
   def my_function(ctx: AnimationContext) -> None:
       pass
   ```

3. **Passer ctx plutôt que d'accéder au proxy**
   ```python
   # Moins bon (utilise proxy)
   def animate_track(track):
       fps = glb.fps
       for note in track.notes:
           frame = note.time * fps
   
   # Meilleur (utilise ctx explicite)
   def animate_track(track, ctx: AnimationContext):
       fps = ctx.fps
       for note in track.notes:
           frame = note.time * fps
   ```

4. **Documenter les dépendances**
   ```python
   def process_animation(ctx: AnimationContext) -> None:
       """Process animation.
       
       Requires ctx.tracks and ctx.fps to be initialized.
       Sets ctx.last_note_time_off.
       """
       pass
   ```

## Support et questions

Pour plus d'informations :
- Lire `REFACTORING.md` pour les changements complets
- Consulter `m2v/engine/context.py` pour l'implémentation
- Vérifier les usages dans `m2v/ext/ops.py` pour des exemples réels
