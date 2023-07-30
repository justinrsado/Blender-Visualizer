# Blender-Visualizer
Script for using audio to animate objects in Blender.

Run this script in Blender's scripting workspace to register the Visualizer sidebar panel; clicking the Visualize button will generate five objects in a collection, with their z-axis scales keyframed to sync with filtered bins of any audio in the sequencer (from the scene's start-frame to its end-frame). This data can then be accessed with an Object Info node in geometry nodes.

Note: Error cases haven't been accounted for, so having the system console toggled on is a good idea (Window->Toggle System Console).