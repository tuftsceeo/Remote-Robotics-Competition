import cv2
import numpy as np
import apriltag
import websocket
import ssl
import json
import time
from IPython.display import display, Javascript
from google.colab.output import eval_js
from base64 import b64decode, b64encode
import PIL
import io
import ipywidgets as widgets

class wss_CEEO():
    def __init__(self, url):
        self.url = url
    
    def send_message(self, message):
        ws = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
        try:
            ws.connect(self.url)
            ws.send(json.dumps(message))
            print(f"Sent: {message}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            ws.close()

class AprilTagDetector:
    def __init__(self):
        self.uri = "wss://chrisrogers.pyscriptapps.com/talking-on-a-channel/api/channels/hackathon"
        self.selected_topic = "Car_Location_1"
        self.is_running = False
        self.detector = apriltag.Detector(apriltag.DetectorOptions(families="tag36h11"))
        self.ws_client = None
    
    def setup_websocket(self):
        self.ws_client = wss_CEEO(self.uri)
    
    def calculate_rotation(self, corners):
        dx = corners[1][0] - corners[0][0]  
        dy = corners[1][1] - corners[0][1]
        return float(np.degrees(np.arctan2(dy, dx)))
    
    def send_apriltag_data(self, tag_data):
        if not tag_data or not self.ws_client:
            return
            
        for tag in tag_data:
            message = {
                'topic': f'/{self.selected_topic}/All',
                'value': {
                    'x': round(tag['x'], 3), 
                    'y': round(tag['y'], 3), 
                    'rotation': round(tag['rotation'], 3)
                }
            }
            self.ws_client.send_message(message)

def video_stream():
    js = Javascript('''
        var video, div = null, stream, captureCanvas, imgElement, labelElement;
        var pendingResolve = null, shutdown = false;
        
        function removeDom() {
           stream.getVideoTracks()[0].stop();
           video.remove();
           div.remove();
           video = div = stream = imgElement = captureCanvas = labelElement = null;
        }
        
        function onAnimationFrame() {
          if (!shutdown) window.requestAnimationFrame(onAnimationFrame);
          if (pendingResolve) {
            var result = "";
            if (!shutdown) {
              captureCanvas.getContext('2d').drawImage(video, 0, 0, 640, 480);
              result = captureCanvas.toDataURL('image/jpeg', 0.8)
            }
            var lp = pendingResolve;
            pendingResolve = null;
            lp(result);
          }
        }
        
        async function createDom() {
          if (div !== null) return stream;

          div = document.createElement('div');
          div.style.border = '2px solid black';
          div.style.padding = '3px';
          div.style.width = '100%';
          div.style.maxWidth = '600px';
          document.body.appendChild(div);
          
          const modelOut = document.createElement('div');
          modelOut.innerHTML = "<span>Status:</span>";
          labelElement = document.createElement('span');
          labelElement.innerText = 'No data';
          labelElement.style.fontWeight = 'bold';
          modelOut.appendChild(labelElement);
          div.appendChild(modelOut);
               
          video = document.createElement('video');
          video.style.display = 'block';
          video.width = div.clientWidth - 6;
          video.setAttribute('playsinline', '');
          video.onclick = () => { shutdown = true; };
          stream = await navigator.mediaDevices.getUserMedia({video: { facingMode: "environment"}});
          div.appendChild(video);

          imgElement = document.createElement('img');
          imgElement.style.position = 'absolute';
          imgElement.style.zIndex = 1;
          imgElement.onclick = () => { shutdown = true; };
          div.appendChild(imgElement);
          
          const instruction = document.createElement('div');
          instruction.innerHTML = '<span style="color: red; font-weight: bold;">When finished, click here or on the video to stop this demo</span>';
          div.appendChild(instruction);
          instruction.onclick = () => { shutdown = true; };
          
          video.srcObject = stream;
          await video.play();

          captureCanvas = document.createElement('canvas');
          captureCanvas.width = 640;
          captureCanvas.height = 480;
          window.requestAnimationFrame(onAnimationFrame);
          
          return stream;
        }
        
        async function stream_frame(label, imgData) {
          if (shutdown) {
            removeDom();
            shutdown = false;
            return '';
          }

          stream = await createDom();
          
          if (label != "") labelElement.innerHTML = label;
                
          if (imgData != "") {
            var videoRect = video.getClientRects()[0];
            imgElement.style.top = videoRect.top + "px";
            imgElement.style.left = videoRect.left + "px";
            imgElement.style.width = videoRect.width + "px";
            imgElement.style.height = videoRect.height + "px";
            imgElement.src = imgData;
          }
          
          var result = await new Promise(function(resolve, reject) {
            pendingResolve = resolve;
          });
          shutdown = false;
          
          return {'img': result};
        }
        
        function stopVideoStream() {
          shutdown = true;
        }
        ''')
    display(js)
  
def video_frame(label, bbox):
    return eval_js('stream_frame("{}", "{}")'.format(label, bbox))

def js_to_image(js_reply):
    image_bytes = b64decode(js_reply.split(',')[1])
    jpg_as_np = np.frombuffer(image_bytes, dtype=np.uint8)
    return cv2.imdecode(jpg_as_np, flags=1)

def bbox_to_bytes(bbox_array):
    bbox_PIL = PIL.Image.fromarray(bbox_array, 'RGBA')
    iobuf = io.BytesIO()
    bbox_PIL.save(iobuf, format='png')
    return 'data:image/png;base64,{}'.format(str(b64encode(iobuf.getvalue()), 'utf-8'))

def detect_apriltags(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    results = detector.detector.detect(gray)
    
    tag_data = []
    for r in results:
        tag_data.append({
            'id': r.tag_id,
            'x': float(r.center[0]),
            'y': float(r.center[1]),
            'rotation': detector.calculate_rotation(r.corners)
        })
    
    return results, tag_data

def create_ui():
    global detector, topic_dropdown, start_button, stop_button, status_label
    
    topic_dropdown = widgets.Dropdown(
        options=['Car_Location_1', 'Car_Location_2'],
        value='Car_Location_1',
        description='Topic:',
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='200px')
    )
    
    start_button = widgets.Button(
        description='Start Camera',
        button_style='success',
        layout=widgets.Layout(width='120px')
    )
    
    stop_button = widgets.Button(
        description='Stop Camera',
        button_style='danger',
        layout=widgets.Layout(width='120px'),
        disabled=True
    )
    
    status_label = widgets.HTML(
        value="<b>Status:</b> Ready to start",
        layout=widgets.Layout(width='300px')
    )
    
    def on_topic_change(change):
        detector.selected_topic = change['new']
        status_label.value = f"<b>Status:</b> Topic set to {detector.selected_topic}"
    
    def on_start_click(b):
        start_detection()
    
    def on_stop_click(b):
        stop_detection()
    
    topic_dropdown.observe(on_topic_change, names='value')
    start_button.on_click(on_start_click)
    stop_button.on_click(on_stop_click)
    
    display(widgets.HBox([
        widgets.VBox([topic_dropdown, status_label]),
        widgets.VBox([start_button, stop_button])
    ]))

def start_detection():
    detector.is_running = True
    detector.setup_websocket()
    start_button.disabled = True
    stop_button.disabled = False
    status_label.value = f"<b>Status:</b> Detecting on {detector.selected_topic}"
    
    video_stream()
    
    try:
        detection_loop()
    except Exception as e:
        print(f"Detection error: {e}")
        stop_detection()

def stop_detection():
    detector.is_running = False
    start_button.disabled = False
    stop_button.disabled = True
    status_label.value = "<b>Status:</b> Stopped"
    
    try:
        eval_js('stopVideoStream()')
    except:
        pass

def detection_loop():
    bbox = ''
    last_send_time = time.time()
    send_interval = 0.1
    bbox_array = np.zeros([480,640,4], dtype=np.uint8)
    
    while detector.is_running:
        try:
            js_reply = video_frame('Detecting AprilTags...', bbox)
            if not js_reply:
                break

            img = js_to_image(js_reply["img"])
            results, tag_data = detect_apriltags(img)
            
            bbox_array.fill(0)
            bbox = ''

            if results:
                for r in results:
                    (cX, cY) = (int(r.center[0]), int(r.center[1]))
                    cv2.circle(bbox_array, (cX, cY), 5, (0, 0, 255), -1)
                    cv2.putText(bbox_array, f"ID: {r.tag_id}", (int(r.corners[0][0]), int(r.corners[0][1]) - 15),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

                bbox_array[:,:,3] = (bbox_array.max(axis=2) > 0).astype(int) * 255
                bbox = bbox_to_bytes(bbox_array)

            current_time = time.time()
            if tag_data and (current_time - last_send_time) > send_interval:
                detector.send_apriltag_data(tag_data)
                last_send_time = current_time

        except Exception as e:
            print(f"Detection error: {e}")
            detector.is_running = False
            break
    
    stop_detection()

def main():
    global detector
    detector = AprilTagDetector()
    create_ui()

detector = None
topic_dropdown = None
start_button = None
stop_button = None
status_label = None

if __name__ == "__main__":
    main()
