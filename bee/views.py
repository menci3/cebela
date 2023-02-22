from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, StreamingHttpResponse, FileResponse
from django.urls import reverse
from django.contrib import messages
from django.views.decorators import gzip
from pathlib import Path
from datetime import datetime, timedelta
import pytz
import cv2
import threading
import torch
import cpuinfo

from django.conf import settings
from .models import Detections, Settings
from Yolov5_StrongSORT_OSNet.track import run


class Tracking(object):
    def __init__(self):
        self.image = cv2.imread('bee/static/bee/placeholder.jpg', 0)
        self.running = False
        self.show_lines = True
        self.start_time = None

    def get_frame(self):
        _, jpeg = cv2.imencode('.jpg', self.image)
        return jpeg.tobytes()

    def start(self):
        setting = Settings.objects.all().first()

        self.start_time = setting.start_time

        if setting is None:
            return 'Manjkajoče nastavitve'

        arguments = {
            'source': setting.source,
            'yolo_weights': Path(setting.weights),
            'imgsz': (setting.img_size_y, setting.img_size_x),
            'tracking_method': setting.tracking_method,
            'show_vid': True,
            'device': setting.device if setting.device > -1 else 'cpu',
            'tracking': self,
        }

        threading.Thread(target=run, kwargs=arguments).start()

        self.running = True

        return 'V teku'

    def stop(self):
        self.image = cv2.imread('bee/static/bee/placeholder.jpg', 0)
        self.running = False
        return 'Nedejavno'

    def status(self):
        if self.running is False:
            return 'Nedejavno'

        return 'V teku'

    def update(self, image):
        self.image = image

    def hide_lines(self):
        self.show_lines = False

    def create_detection(self, date, delta_visit, delta_visit_pollen, delta_leave, delta_leave_pollen):
        self.show_lines = False

        detection = Detections(
            date=date,
            visit=delta_visit,
            visit_pollen=delta_visit_pollen,
            leave=delta_leave,
            leave_pollen=delta_leave_pollen)

        detection.save()


class Video(object):
    def __init__(self):
        self.video = None
        self.frame = cv2.imread('bee/static/bee/placeholder.jpg', 0)
        self.state = 'Off'
        self.running = False
        self.frame_rate = 0

    def __del__(self):
        if self.video is not None:
            self.video.release()

    def get_frame(self):
        image = self.frame
        if image is None:
            image = cv2.imread('bee/static/bee/placeholder.jpg', 0)
        _, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def start(self):
        setting = Settings.objects.all().first()

        self.running = True
        self.state = 'Running'

        if self.video is not None:
            self.video.release()

        self.video = cv2.VideoCapture(setting.source)

        if Path(setting.source).is_file():
            self.frame_rate = self.video.get(cv2.CAP_PROP_FPS)
        else:
            self.frame_rate = 0

        threading.Thread(target=self.update, args=()).start()

    def resume(self):
        self.running = True
        self.state = 'Running'

        threading.Thread(target=self.update, args=()).start()

    def stop(self):
        self.running = False
        self.state = 'Stopped'

    def update(self):
        while self.running:
            (self.grabbed, self.frame) = self.video.read()
            if self.frame is None:
                break
            if self.frame_rate > 0:
                cv2.waitKey(int(1000 / self.frame_rate))


tracking = Tracking()
video = Video()


def video_stop(request):
    global video
    video.stop()
    return HttpResponse('Stop')


def video_start(request):
    global video
    video.start()
    return HttpResponse('Start')


def video_resume(request):
    global video
    video.resume()
    return HttpResponse('Resume')


def index(request):
    global tracking
    global video
    cet = pytz.timezone(settings.TIME_ZONE)

    today = datetime.now(cet)
    today_start = datetime.combine(today.date(), datetime.min.time(), today.tzinfo)

    detections = Detections.objects.filter(date__gte=today_start)

    visit_sum = 0
    visit_pollen_sum = 0
    leave_sum = 0

    timestamps = []

    visit = []
    visit_pollen = []
    leave = []
    leave_pollen = []

    for data in detections:
        visit_sum += data.visit
        visit_pollen_sum += data.visit_pollen
        leave_sum += data.leave + data.leave_pollen

        timestamps.append(data.date.astimezone(cet).strftime('%m/%d/%Y, %H:%M:%S'))
        visit.append(data.visit)
        visit_pollen.append(data.visit_pollen)
        leave.append(data.leave)
        leave_pollen.append(data.leave_pollen)

    visit_all_sum = visit_sum + visit_pollen_sum
    day_delta = visit_all_sum - leave_sum

    setting = Settings.objects.all().first()

    if Path(setting.source).is_file():
        video_type = 'file'
    elif setting.source[0:7] == 'rtsp://':
        video_type = 'rtsp'
    else:
        video_type = 'unsupported'

    if setting.device == -1:
        device = cpuinfo.get_cpu_info()['brand_raw']
    else:
        device = torch.cuda.get_device_name(setting.device)

    context = {'visit': visit, 'visit_pollen': visit_pollen, 'leave': leave, 'leave_pollen': leave_pollen,
               'visit_sum': visit_sum, 'visit_pollen_sum': visit_pollen_sum, 'visit_all_sum': visit_all_sum,
               'leave_sum': leave_sum, 'day_delta': day_delta, 'timestamps': timestamps,
               'source': setting.source.split("/")[-1], 'weights': setting.weights.split("/")[-1],
               'tracking_method': setting.tracking_method, 'device': device, 'img_size_x': setting.img_size_x,
               'img_size_y': setting.img_size_y, 'running': tracking.running, 'video_state': video.state,
               'video_type': video_type}

    return render(request, 'bee/index.html', context)


def stats(request):
    global tracking

    detections = []

    timestamps = []

    visit = []
    visit_pollen = []
    leave = []
    leave_pollen = []

    view = request.GET.get("view")

    try:
        if view == 'date':
            date = datetime.strptime(request.GET.get("date"), '%Y-%m-%d')
            detections = Detections.objects.filter(date__year=date.year, date__month=date.month, date__day=date.day)
        elif view == 'month':
            date = datetime.strptime(request.GET.get("date"), '%Y-%m')
            detections = Detections.objects.filter(date__year=date.year, date__month=date.month)
        elif view == 'year':
            date = datetime.strptime(request.GET.get("date"), '%Y')
            detections = Detections.objects.filter(date__year=date.year)
    except Exception as e:
        print(e)

    cet = pytz.timezone(settings.TIME_ZONE)

    for detection in detections:
        timestamps.append(detection.date.astimezone(cet).strftime('%m/%d/%Y, %H:%M:%S'))
        visit.append(detection.visit)
        visit_pollen.append(detection.visit_pollen)
        leave.append(detection.leave)
        leave_pollen.append(detection.leave_pollen)

    context = {'timestamps': timestamps, 'visit': visit, 'visit_pollen': visit_pollen, 'leave': leave,
               'leave_pollen': leave_pollen, 'view': view, 'running': tracking.running}

    return render(request, 'bee/stats.html', context)


def settings_view(request):
    global tracking

    setting = Settings.objects.all().first()

    if setting is not None:
        devices = [cpuinfo.get_cpu_info()['brand_raw']]

        if torch.cuda.is_available() and torch.cuda.device_count():
            for gpu_index in range(0, torch.cuda.device_count()):
                devices.append(torch.cuda.get_device_name(gpu_index))

        cet = pytz.timezone(settings.TIME_ZONE)
        formatted_date = setting.start_time.astimezone(cet).strftime('%Y-%m-%dT%H:%M:%S')

        context = {'source': setting.source, 'weights': setting.weights, 'selected_method': setting.tracking_method,
                   'selected_device': setting.device + 1, 'devices': devices, 'img_size_x': setting.img_size_x,
                   'img_size_y': setting.img_size_y, 'start_time': formatted_date, 'running': tracking.running}

    else:
        context = {'running': tracking.running}

    return render(request, 'bee/settings.html', context)


def settings_update(request):
    if request.method == 'POST':
        if request.POST['source'][0:7] != 'rtsp://' and not Path(request.POST['source']).is_file():
            messages.error(request, 'Vhodna datoteka ne obstaja!')
        elif not Path(request.POST['weights']).is_file():
            messages.error(request, 'Datoteka z utežmi ne obstaja!')
        else:
            setting = Settings.objects.all().first()

            if setting is None:
                setting = Settings()

            try:
                setting.source = request.POST['source']
                setting.weights = request.POST['weights']
                setting.tracking_method = request.POST['tracking_method']
                setting.img_size_x = int(request.POST['image_size_x'])
                setting.img_size_y = int(request.POST['image_size_y'])
                setting.start_time = request.POST['start_time']
                setting.device = int(request.POST['device']) - 1

                setting.save()

                messages.success(request, 'Nastavitve spremenjene.')
            except ValueError as e:
                print(e)
                messages.error(request, 'Napačno vneseni podatki podatki.')
            except Exception as e:
                print(e)
                messages.error(request, 'Napaka pri shranjevanju nastavitev.')

        return HttpResponseRedirect(reverse('bee:settings_view'))


def tracking_start(request):
    if request.method == 'POST':
        global tracking
        return HttpResponse(tracking.start())


def tracking_stop(request):
    if request.method == 'POST':
        global tracking

        return HttpResponse(tracking.stop())


@gzip.gzip_page
def video_stream(request):
    global video

    try:
        return StreamingHttpResponse(gen(video), content_type="multipart/x-mixed-replace;boundary=frame")
    except Exception as e:
        print(e)

    return FileResponse(open('bee/static/bee/placeholder.jpg', 'rb'))


def tracking_view(request):
    global tracking
    return render(request, 'bee/tracking.html', {'running': tracking.running})


def tracking_status(request):
    global tracking
    return HttpResponse(tracking.status())


@gzip.gzip_page
def tracking_stream(request):
    global tracking

    try:
        return StreamingHttpResponse(gen(tracking), content_type="multipart/x-mixed-replace;boundary=frame")
    except Exception as e:
        print(e)

    return FileResponse(open('bee/static/bee/placeholder.jpg', 'rb'))


def gen(video_source):
    while True:
        frame = video_source.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
