# Boxlet

Boxlet is a module used alongside pygame for quickly and easily setting up new projects.
The module contains an simple, but effective, entity system and extensive classes for creating a rendering system in OpenGL or Vulkan.

The entity system features
- function tracking for
  - fixed time interval updates
  - variable time interval updates
  - pygame event triggers
  - render events
  - on destroy events
- per class/function priority call order
- getting a list of entities of a given subclass

The module is still in the early stages of development, but is still usable.  Feedback or contrubutions would be appreciated.

## Rendering Systems

The OpenGL and Vulkan implementations are designed so that you can create an entire rendering system with very few lines of code AND without touching the respective graphics libraries.
You can still replace individual parts of the built in classes with your own versions to better suit your application's needs.

Each version will eventually have their own README file that will give an overview of how the rendering systems are used.

### OpenGL

The opengl classes require PyOpenGL ( https://github.com/mcfletch/pyopengl ) and work with Windows and Mac.
Though linux needs some testing.
Also, as a reminder, Mac is either limited to versions 3.3 or 4.1 of OpenGL.

### Vulkan

The vulkan classes requires the Vulkan SDK and the Python binding for Vulkan by realitix ( https://github.com/realitix/vulkan ).
The current implementation only seems to work with Windows at the moment.
A most of the code I started with came from the youtube channel GetIntoGameDev (https://www.youtube.com/watch?v=2NVlG9TFT1c&list=PLn3eTxaOtL2M4qgHpHuxY821C_oX0GvM7&index=2), 
but it has been heavily modified and extended to better fit the renderer's needs and normal python conventions.
