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
        except:
            pass
        finally:
            ws.close()

class AprilTagDetector:
    def __init__(self):
        self.uri = "wss://chrisrogers.pyscriptapps.com/talking-on-a-channel/api/channels/hackathon"
        self.selected_topic = "Car_Location_1"
        self.is_running = False
        self.ws_client = None
        
        # Pre-initialize detector for better performance
        options = apriltag.DetectorOptions(families="tag36h11")
        self.detector = apriltag.Detector(options)
        
        # Pre-allocate arrays for better performance
        self.bbox_array = np.zeros([480, 640, 4], dtype=np.uint8)
        self.last_send_time = 0
        self.send_interval = 0.05  # Faster updates - 50ms
        
    def setup_websocket(self):
        self.ws_client = wss_CEEO(self.uri)
    
    def send_apriltag_data(self, tag_data):
        if not tag_data or not self.ws_client:
            return
            
        for tag in tag_data:
            message = {
                'topic': f'/{self.selected_topic}/All',
                'value': {
                    'tag_id': tag['id'],
                    'x': tag['x'], 
                    'y': tag['y'], 
                    'rotation': tag['rotation']
                }
            }
            self.ws_client.send_message(message)

def video_stream():
    js = Javascript('''
        var video, div = null, stream, captureCanvas, imgElement, labelElement;
        var pendingResolve = null, shutdown = false;
        
        function removeDom() {
           if(stream) stream.getVideoTracks()[0].stop();
           if(video) video.remove();
           if(div) div.remove();
           video = div = stream = imgElement = captureCanvas = labelElement = null;
        }
        
        function onAnimationFrame() {
          if (!shutdown) window.requestAnimationFrame(onAnimationFrame);
          if (pendingResolve) {
            var result = "";
            if (!shutdown && captureCanvas && video) {
              captureCanvas.getContext('2d').drawImage(video, 0, 0, 640, 480);
              result = captureCanvas.toDataURL('image/jpeg', 0.7); // Lower quality for speed
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
          labelElement.innerText = 'Initializing...';
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
          instruction.innerHTML = '<span style="color: red; font-weight: bold;">Click to stop</span>';
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
          
          if (label != "" && labelElement) labelElement.innerHTML = label;
                
          if (imgData != "" && imgElement && video) {
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
        
        function stopVideoStream() { shutdown = true; }
        ''')
    display(js)
  
def video_frame(label, bbox):
    data = eval_js('stream_frame("{}", "{}")'.format(label, bbox))
    return data

def js_to_image(js_reply):
    image_bytes = b64decode(js_reply.split(',')[1])
    jpg_as_np = np.frombuffer(image_bytes, dtype=np.uint8)
    return cv2.imdecode(jpg_as_np, flags=1)

def bbox_to_bytes(bbox_array):
    bbox_PIL = PIL.Image.fromarray(bbox_array, 'RGBA')
    iobuf = io.BytesIO()
    bbox_PIL.save(iobuf, format='png')
    return 'data:image/png;base64,{}'.format(str(b64encode(iobuf.getvalue()), 'utf-8'))

def detect_apriltags(image, detector_instance):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    results = detector_instance.detector.detect(gray)
    
    tag_data = []
    for r in results:
        # Simplified rotation calculation
        dx = r.corners[1][0] - r.corners[0][0]  
        dy = r.corners[1][1] - r.corners[0][1]
        rotation = float(np.degrees(np.arctan2(dy, dx)))
        
        tag_data.append({
            'id': r.tag_id,
            'x': round(float(r.center[0]), 1),
            'y': round(float(r.center[1]), 1),
            'rotation': round(rotation, 1)
        })
    
    return results, tag_data

def create_ui():
    global detector, topic_dropdown, start_button, stop_button, status_label
    
    topic_dropdown = widgets.Dropdown(
        options=['Car_Location_1', 'Car_Location_2'],
        value='Car_Location_1',
        description='Topic:'
    )
    
    start_button = widgets.Button(description='Start', button_style='success')
    stop_button = widgets.Button(description='Stop', button_style='danger', disabled=True)
    status_label = widgets.HTML(value="<b>Ready</b>")
    
    def on_channel_change(change):
        detector.selected_topic = change['new']
    
    def on_start_click(b):
        start_detection()
    
    def on_stop_click(b):
        stop_detection()
    
    topic_dropdown.observe(on_channel_change, names='value')
    start_button.on_click(on_start_click)
    stop_button.on_click(on_stop_click)
    
    ui = widgets.HBox([topic_dropdown, start_button, stop_button, status_label])
    display(ui)

def start_detection():
    global detector
    
    detector.is_running = True
    detector.setup_websocket()
    start_button.disabled = True
    stop_button.disabled = False
    status_label.value = f"<b>Streaming to {detector.selected_topic}</b>"
    
    video_stream()
    
    try:
        detection_loop()
    except:
        stop_detection()

def stop_detection():
    global detector
    
    detector.is_running = False
    start_button.disabled = False
    stop_button.disabled = True
    status_label.value = "<b>Stopped</b>"
    
    try:
        eval_js('stopVideoStream()')
    except:
        pass

def detection_loop():
    global detector
    
    bbox = ''
    frame_count = 0
    
    while detector.is_running:
        try:
            js_reply = video_frame('Scanning...', bbox)
            if not js_reply:
                break

            img = js_to_image(js_reply["img"])
            results, tag_data = detect_apriltags(img, detector)
            
            # Only create overlay if tags detected
            if results:
                # Fast array reset
                detector.bbox_array.fill(0)
                
                # Minimal drawing for performance
                for r in results:
                    cX, cY = int(r.center[0]), int(r.center[1])
                    cv2.circle(detector.bbox_array, (cX, cY), 4, (0, 255, 0, 255), -1)
                    
                    # Simple text
                    ptA = (int(r.corners[0][0]), int(r.corners[0][1]))
                    cv2.putText(detector.bbox_array, str(r.tag_id), (ptA[0], ptA[1] - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0, 255), 2)

                detector.bbox_array[:,:,3] = (detector.bbox_array.max(axis=2) > 0).astype(int) * 255
                bbox = bbox_to_bytes(detector.bbox_array)
                
                label = f'Tags: {len(results)}'
            else:
                bbox = ''
                label = 'Scanning...'

            # Throttled websocket sending
            current_time = time.time()
            if tag_data and (current_time - detector.last_send_time) > detector.send_interval:
                detector.send_apriltag_data(tag_data)
                detector.last_send_time = current_time

            frame_count += 1

        except:
            break
    
    stop_detection()

def main():
    global detector
    detector = AprilTagDetector()
    create_ui()

# Global variables
detector = None
topic_dropdown = None
start_button = None
stop_button = None
status_label = None

main()
