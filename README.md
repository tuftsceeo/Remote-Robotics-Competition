# Remote-Robotics-Competition

## Authors:
Tufts Center for Engineering Education and Outreach \
Prof. Chris Rogers FET Lab \
[William Goldman](https://www.goldmanwilliam.com/), [Conor Temme](https://www.linkedin.com/in/conor-temme-2b024a321/)

## Date:
Summer 2025 (June-July)

## Documentation
For a complete overview of the project, visit this [Notion page](https://fetlab.notion.site/Remote-FLL-Competition-237df3d0e05280e09622c856f06f14f7)

## What's in this repository

General Tools:
- Apriltag detection
- Camera streaming
- Hardware connection
- Keyboard control

Pyscript.com code for three game demos:
- Mario Kart
- Painting Demo
- Team Scoring Demo

# General Tools

* [Car/](.\General Tools\Car)
  * [Science_Hardware/](.\General Tools\Car\Science_Hardware)
    * [car_talkingonahub.py](.\General Tools\Car\Science_Hardware\car_talkingonahub.py)
  * [SPIKE/](.\General Tools\Car\SPIKE)
    * [car_spike.py](.\General Tools\Car\SPIKE\car_spike.py)
    * [car_web.py](.\General Tools\Car\SPIKE\car_web.py)
* [Controller/](.\General Tools\Controller)
  * [Science_Hardware/](.\General Tools\Controller\Science_Hardware)
    * [controller_talkingonahub.py](.\General Tools\Controller\Science_Hardware\controller_talkingonahub.py)
  * [SPIKE/](.\General Tools\Controller\SPIKE)
    * [talking_on_anyone/](.\General Tools\Controller\SPIKE\talking_on_anyone)
      * [controller_spike.py](.\General Tools\Controller\SPIKE\talking_on_anyone\controller_spike.py)
      * [controller_web.py](.\General Tools\Controller\SPIKE\talking_on_anyone\controller_web.py)
    * [talking_on_a_hub/](.\General Tools\Controller\SPIKE\talking_on_a_hub)
      * [controller_web.py](.\General Tools\Controller\SPIKE\talking_on_a_hub\controller_web.py)
* [OpenMV/](.\General Tools\OpenMV)
  * [apriltag_detection/](.\General Tools\OpenMV\apriltag_detection)
    * [apriltag_identify.py](.\General Tools\OpenMV\apriltag_detection\apriltag_identify.py)
    * [apriltag_post_to_channel.py](.\General Tools\OpenMV\apriltag_detection\apriltag_post_to_channel.py)
    * [apriltag_post_to_channel_ALL.py](.\General Tools\OpenMV\apriltag_detection\apriltag_post_to_channel_ALL.py)
  * [streaming/](.\General Tools\OpenMV\streaming)
    * [all_in_one_file.py](.\General Tools\OpenMV\streaming\all_in_one_file.py)
    * [main_code.py](.\General Tools\OpenMV\streaming\main_code.py)
    * [websocket.py](.\General Tools\OpenMV\streaming\websocket.py)
* [Webcam Apriltag/](.\General Tools\Webcam Apriltag)
  * [google_colab_imports.py](.\General Tools\Webcam Apriltag\google_colab_imports.py)
  * [google_colab_main.py](.\General Tools\Webcam Apriltag\google_colab_main.py)
  * [vscode_apriltag.py](.\General Tools\Webcam Apriltag\vscode_apriltag.py)

## General Setup
<img width="768" height="960" alt="Demo Field Setup (Marked up)" src="https://github.com/user-attachments/assets/a852e497-4ce9-4f83-8204-5747bae7b5e6" />

## Other notes
- Some of the code in 'General Tools' is still specific to the Mario Kart demo (i.e. the LEGO SPIKE car listening to /Peel) but the general motor control can be used across demos
