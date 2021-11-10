# SupercellSWF

Version 0.1.0.1

## About

Editing tool (read/write) .sc files (*_tes.sc , *.sc, *_dl.sc ) from Supercell games (Brawl Stars, Clash Royale, Clash of Clans and others). This is a test version, so it may contain bugs (if you find it, please write about it to me in Discord or Issues). Special thanks to Selce for some information about .sc and Vorono4ka for his sc-compression module (also some parts of working with textures were based on his code, don't forget..).


## Install
```sh 
pip install SupercellSWF
```

## How to

### Load .sc files

```python 
from sc import SupercellSWF

swf = SupercellSWF()
swf.load("path/to/file.sc")

# code...

```

Also, in some cases, you may not load the texture file (made for convenience). Because you may not have this file or you don't need to edit textures.

```python 
swf.load("path/to/file.sc", load_texture_file = False)
```

### Save .sc files

```python 
# ...code

swf.save("save/path/file.sc")
```

And

```python 
swf.save("save/path/file.sc", save_texture_file = False)
```

## SC Objects

A little bit about SC objects. For minimal work, you only need SWFTexture, Shape, TextField, MovieClipModifier and MovieClip, more specifically about the objects themselves later. Each of these listed objects (except SWFTexture) has its own id (obj.export_id), each must have its own non-repeating id!! (unfortunately, they will have to be set manually, but perhaps in the future I will do their auto generation).

```python 
from sc import SWFTexture, Shape, TextField, MovieClipModifier, MovieClip
from PIL import Image


img = Image.open("path/to/image.png")

texture = SWFTexture()
texture.from_image(img)


shape = Shape()
shape.export_id = 0

txt = TextField()
txt.export_id = 1

modifier = MovieClipModifier()
modifier.export_id = 2

clip = MovieClip()
clip.export_id = 3

```

There will be more information soon...

# Warning

This content is not affiliated with, endorsed, sponsored, or specifically approved by Supercell and Supercell is not responsible for it. Everything made for fun!
