from scipy.io import wavfile
import numpy as np
import pygame as py
from scipy.fft import fft, fftfreq
import matplotlib
from matplotlib import pyplot as plt
import math
import librosa


VALUES_PER_SECOND = 20
FPS = 120.0

DELTA = VALUES_PER_SECOND/FPS

def hsv_to_rgb(h, s, v):
    if s == 0.0:
        r = g = b = int(v * 255)
        return r, g, b

    h = h / 60.0
    i = int(h)
    f = h - i
    p = int(v * (1.0 - s) * 255)
    q = int(v * (1.0 - s * f) * 255)
    t = int(v * (1.0 - s * (1.0 - f)) * 255)
    v = int(v * 255)

    if i == 0:
        return v, t, p
    elif i == 1:
        return q, v, p
    elif i == 2:
        return p, v, t
    elif i == 3:
        return p, q, v
    elif i == 4:
        return t, p, v
    elif i == 5:
        return v, p, q


class Visualizer():
    def __init__(self, song):
        self.song = song
        self.samplerate, data = wavfile.read(song)


        #Debug - show samplerate
        #print(samplerate)

        self.duration_in_sec = librosa.get_duration(filename=song)


    
        try:
            _, self.num_of_channels = data.shape
        except:
            self.num_of_channels = 1

        if self.num_of_channels == 1:
            self.ydata_for_line = list(data)
            ydata = list(np.array_split(data, VALUES_PER_SECOND * self.duration_in_sec))

        else:
            self.ydata_for_line = list(data[:,0])
            ydata = list(np.array_split(data[:,1], VALUES_PER_SECOND * self.duration_in_sec))


        self.start = 0
        self.y_origin = 500


        #Lists for x and y axi of frequency display
        self.xf_list = []
        self.yf_list = []

        #Getting the frequency spectrum
        for data in ydata:
            normalized_data = np.int16((data / data.max()) * 32767)
            N = data.size

            yf = list(np.abs(fft(normalized_data)))
            xf = list(fftfreq(N, 1 / self.samplerate))

            self.xf_list.append(xf)
            self.yf_list.append(yf)


        #Debug - show frequency spectrum of an instant (0), on a plot
        #plt.plot(np.resize(xf_list[0],15031), np.abs(yf_list[0]))
        #plt.show()

        #Debug - Show frequency range
        #print(len(xf_list))


        py.init()
        py.mixer.init(self.samplerate, -16, 1, 1024)

        self.screen = py.display.set_mode((640,640))

        self.clock = py.time.Clock()


        py.mixer.music.load(song)

        self.bars = [0 for i in range(1640)]

    def play(self):
        self.count = 0

        self.run = True

        print("running...")

        while self.run:
            self.screen.fill((0,0,0))

            for e in py.event.get():
                if e.type == py.QUIT:
                    self.run = False


            #Frame count to move the visualization at the same rate the song plays
            self.count += DELTA

            if py.mixer.get_busy():
                music_start_time = py.mixer.music.get_pos() / 1000.0  # Convert milliseconds to seconds



            #Get x and y axi of the specturm for the current instant
            xf, yf = self.xf_list[int(self.count)], self.yf_list[int(self.count)]

            #Drawing the raw data in points
            '''for i in range(len(xf)):
                py.draw.circle(self.screen, (255,255,255), (10+xf[i]/40, 300-yf[i]/30000), 1)'''

            #Drawing the raw data in points, as polygon (not working rn)
            '''points = [(10+xf[i]/80, 300-yf[i]/30000) for i in range(len(xf))]
            points.append((640, 300))
            points.append((0,300))

            py.draw.polygon(self.screen, (100,100,255), points)'''


            #Drawing the bars, which each are the average of five points
            for i in range(int(len(xf)/5)):
                val = 0
                for j in range(5):
                    val += yf[i+j]/30000
                val/=5

                self.bars[i] += max(0, val - self.bars[i])

            for i, bar in enumerate(self.bars):
                if i < len(xf)/5:
                    color = hsv_to_rgb(i/len(xf) * 360 * 2.5, 1, .8)

                    py.draw.line(self.screen, color, (10+xf[i]/16, 200-bar * i / 100), (10+xf[i]/16, 200), 2)
                    self.bars[i] -= self.bars[i] * .98 / FPS * 20
                    if self.bars[i] < 0:
                        self.bars[i] = 0

            #Drawing the bars but in a circle
            for i in range(int(len(xf)/5)):
                val = 0
                for j in range(5):
                    val += yf[i+j]/30000 
                val/=5

                ag = xf[i] * math.pi / 4400 

                module_ = val

                color = hsv_to_rgb(i/len(xf) * 360 * 5, 1, .8)

                py.draw.line(self.screen, color, (300+math.cos(ag)*50,400+ math.sin(ag)*50), 
                                (300+math.cos(ag)*(50+self.bars[i] * i / 100 * .5), 400+math.sin(ag)*(50+self.bars[i] * i / 100 * .5)), 1)
            
                py.draw.line(self.screen, color, (300+math.cos(ag)*50,400+ math.sin(ag)*50), 
                                (300+math.cos(ag)*(50 - self.bars[i] * i / 100 * .3), 400+math.sin(ag)*(50 - self.bars[i] * i / 100 * .3)), 1)
                

            '''#Drawing the sound line
            self.start += int(self.samplerate/600)

            last_pos = (0,0)
            for i in range(1000):
                pos = (i*6, self.y_origin - self.ydata_for_line[(i+self.start)*10]/400) #pos_y is every 10th value, divided by 90 to fit
                py.draw.line(self.screen, (255,255,255), pos, last_pos, 1)

                last_pos = pos'''

            #Only start playing the song after the first display is done, so its synced
            if not py.mixer.music.get_busy():
                py.mixer.music.play()
            else:
                print(py.mixer.music.get_pos()/1000.0 - self.count/VALUES_PER_SECOND)

                self.count = py.mixer.music.get_pos() / 1000.0 * VALUES_PER_SECOND


            self.clock.tick(FPS)
            py.display.set_caption("FPS: " + str(int(self.clock.get_fps())))
            py.display.update()

viz = Visualizer("Songs/OneBeer.wav")
viz.play()