import pygame
import random
import numpy as np
from constants import *

class Track:
    def __init__(self, game, length=100, y0=0, space=False):
        self.game = game
        self.length = length
        self.space = space
        self.y0 = y0
        self.features = []
        self.featuresPos = [] # (x, y) coordinate pairs
        self.l = []
        self.x = []
        self.y = []
        self.segments = []
        self.designTrack(length)
        self.buildTrack()
        self.cars1 = game.cars1
        self.cars2 = game.cars2
        self.cars3 = game.cars3
        self.cars = [self.cars2, self.cars3]
        self.space = space
        self.segmentImagesFront = game.segmentImagesFront
        self.segmentImagesBack = game.segmentImagesBack
        self.segmentImagesFront1 = game.segmentImagesFront1
        self.segmentImagesFront2 = game.segmentImagesFront2
        self.segmentImagesBack1 = game.segmentImagesBack1
        self.popcorn = game.popcorn

    def designTrack(self, length):
        if self.space:
            dx = 40
            dy = -100
            x, y, l = dx, dy+self.y0, np.sqrt(dx*dx+dy*dy)
            self.features.append(('track', -dx, self.y0, dx, 0))
            self.features.append(('track', 0, self.y0, dx, dy))
            self.l = np.array([dx, l+dx])
            self.x = np.array([0, x])
            self.y = np.array([0, y])
            return
        x = 0
        y = self.y0
        l = 0
        while x < self.length:
            f = random.randint(0,20)
            if f < 8:
                x, y, dl = self.addTrack(x, y)
            elif f < 10:
                x, y, dl = self.addLoop(x, y)
            else:
                continue
            l += dl
            self.l.append(l)
            self.x.append(x)
            self.y.append(y)
        self.l = np.array(self.l)
        self.x = np.array(self.x)
        self.y = np.array(self.y)

    def addTrack(self, x0, y0):
        dx = random.randint(5,15)
        dy = random.randint(-2*dx,2*dx)
        if y0 - self.y0 > 5:
            dy = -abs(dy)
        elif y0 - self.y0 <-5:
            dy = abs(dy)
        self.features.append(('track', x0, y0, dx, dy))
        return (dx+x0, dy+y0, np.sqrt(dx*dx+dy*dy))

    def addLoop(self, x0, y0):
        d = random.randint(20,20)
        self.features.append(('loop', x0, y0, d))
        return (d+x0, y0, d*np.pi+d)

    def closeTrack(self):
        x0, y0, theta0 = self.segments[0]
        x1, y1, theta1 = self.segments[-1]
        while abs(y1-y0) > 0.1 or abs((theta0-theta1+180) % 360 - 180) > D_THETA:
            thetaD = max(-60, min(60, -(y0-y1)*10))
            dtheta = (thetaD-theta1+180) % 360 - 180
            theta = (theta1 + min(max(dtheta, -D_THETA), D_THETA)) % 360
            dtheta = (theta-theta1+180) % 360 - 180
            x = x1 + np.cos(np.deg2rad(theta1+dtheta/2))
            y = y1 - np.sin(np.deg2rad(theta1+dtheta/2))
            self.segments.append((x, y, theta))
            self.x_seg.append(x)
            x1, y1, theta1 = self.segments[-1]

    def extendTrack(self, dx):
        x1, y1, theta1 = self.segments[-1]
        self.x_seg = self.x_seg.tolist()
        extra = (dx - int(dx))/int(dx)
        for i in range(int(dx)):
            self.segments.append((x1+i+1+extra*(i+1), y1, 0))
            self.x_seg.append(x1+i+1+extra*(i+1))
        self.x_total = self.segments[-1][0]
        self.x_seg = np.array(self.x_seg)

    def buildTrack(self):
        self.segments.append((0,self.y0,0))
        self.x_seg = [0]
        for l in range(int(self.l[-1])):
            x1, y1, theta1 = self.getPoint(l)
            x0, y0, theta0 = self.segments[-1]
            dtheta = (theta1-theta0+180) % 360 - 180
            theta = (theta0 + min(max(dtheta, -D_THETA), D_THETA)) % 360
            dtheta = (theta-theta0+180) % 360 - 180
            x = x0 + np.cos(np.deg2rad(theta0+dtheta/2))
            y = y0 - np.sin(np.deg2rad(theta0+dtheta/2))
            self.segments.append((x, y, theta))
            self.x_seg.append(x)
        if not self.space:
            self.closeTrack()
        self.x_seg = np.array(self.x_seg)
        self.x_total = self.segments[-1][0]

    def draw(self, screen, origin, playerL, focus=0, enemyLs=[], coinLs=[]):
        if focus == 0:
            imgsF = self.segmentImagesFront1
            imgsB = self.segmentImagesBack1
        elif focus == 1:
            imgsF = self.segmentImagesFront
            imgsB = self.segmentImagesBack
        else:
            imgsF = self.segmentImagesFront2
            imgsB = self.segmentImagesBack
        for l, segment in enumerate(self.segments):
            x, y, theta = segment
            if abs(SCALE*x - origin[0] + self.x_total*SCALE) < MAX_WIDTH/2:
                x += self.x_total
            elif abs(SCALE*x - origin[0] - self.x_total*SCALE) < MAX_WIDTH/2:
                x -= self.x_total
            elif abs(SCALE*x - origin[0]) > MAX_WIDTH/2:
                continue
            if abs(SCALE*y - origin[1]) > MAX_WIDTH/2:
                continue
            angle = int(np.round((theta)/ANG_STEP) % len(self.segmentImagesFront))
            imgB = imgsB[angle]
            imX = SCALE*x - origin[0] - imgB.get_width()/2
            imY = SCALE*y - origin[1] - imgB.get_height()/2
            screen.blit(imgB, (imX+MAX_WIDTH/2, imY+MAX_WIDTH/2))

        if playerL > 0:
            if self.space:
                x, y, theta = self.getPlayerPoint(playerL)
            else:
                x, y, theta = self.segments[int(playerL)]
            angleCar = int(np.round((theta)/ANG_STEP) % len(self.segmentImagesFront))
            imgC = self.cars1[angleCar]
            screen.blit(imgC, (MAX_WIDTH/2-imgC.get_width()/2, MAX_WIDTH/2-imgC.get_height()/2))
            for i in range(3,9,3):
                if self.space:
                    xi, yi, thetai = self.getPlayerPoint(playerL-i)
                else:
                    xi, yi, thetai = self.segments[int(playerL-i)%len(self.segments)]
                angleCar = int(np.round((thetai)/ANG_STEP) % len(self.segmentImagesFront))
                imgC = self.cars[int(i/3-1)][angleCar]
                screen.blit(imgC, (MAX_WIDTH/2-imgC.get_width()/2+SCALE*(xi-x), MAX_WIDTH/2-imgC.get_height()/2+SCALE*(yi-y)))

        for coin in coinLs:
            if coin <= 0:
                continue
            x, y, theta = self.segments[coin]
            if abs(SCALE*x - origin[0] + self.x_total*SCALE) < MAX_WIDTH/2:
                x += self.x_total
            elif abs(SCALE*x - origin[0] - self.x_total*SCALE) < MAX_WIDTH/2:
                x -= self.x_total
            elif abs(SCALE*x - origin[0]) > MAX_WIDTH/2:
                continue
            if abs(SCALE*y - origin[1]) > MAX_WIDTH/2:
                continue
            angle = int(np.round((theta)/ANG_STEP) % len(self.segmentImagesFront))
            imgCoin = self.popcorn[angle]
            imX = SCALE*x - origin[0] - imgCoin.get_width()/2
            imY = SCALE*y - origin[1] - imgCoin.get_height()/2
            screen.blit(imgCoin, (imX+MAX_WIDTH/2, imY+MAX_WIDTH/2))

        for enemy in enemyLs:
            if enemy < 0:
                continue
            x, y, theta = self.getPlayerPoint(int(enemy)%len(self.segments))
            if abs(SCALE*x - origin[0] + self.x_total*SCALE) < MAX_WIDTH/2:
                x += self.x_total
            elif abs(SCALE*x - origin[0] - self.x_total*SCALE) < MAX_WIDTH/2:
                x -= self.x_total
            elif abs(SCALE*x - origin[0]) > MAX_WIDTH/2:
                continue
            if abs(SCALE*y - origin[1]) > MAX_WIDTH/2:
                continue
            angle = int(np.round((theta)/ANG_STEP) % len(self.segmentImagesFront))
            imgEnemy = self.cars[angle]
            imX = SCALE*x - origin[0] - imgEnemy.get_width()/2
            imY = SCALE*y - origin[1] - imgEnemy.get_height()/2
            screen.blit(imgEnemy, (imX+MAX_WIDTH/2, imY+MAX_WIDTH/2))

        for l, segment in enumerate(self.segments):
            x, y, theta = segment
            if abs(SCALE*x - origin[0] + self.x_total*SCALE) < MAX_WIDTH/2:
                x += self.x_total
            elif abs(SCALE*x - origin[0] - self.x_total*SCALE) < MAX_WIDTH/2:
                x -= self.x_total
            elif abs(SCALE*x - origin[0]) > MAX_WIDTH/2:
                continue
            if abs(SCALE*y - origin[1]) > MAX_WIDTH/2:
                continue
            angle = int(np.round((theta)/ANG_STEP) % len(self.segmentImagesFront))
            imgF = imgsF[angle]
            imX = SCALE*x - origin[0] - imgF.get_width()/2
            imY = SCALE*y - origin[1] - imgF.get_height()/2
            screen.blit(imgF, (imX+MAX_WIDTH/2, imY+MAX_WIDTH/2))

    def getPoint(self, l):
        l %= self.l[-1]
        f = np.where(self.l >= l)[0][0]
        if f == 0:
            dl = l
        else:
            dl = l - self.l[f-1]
        if self.features[f][0] == 'track':
            x0, y0, dx, dy = self.features[f][1:]
            x = x0 + dl*dx/np.sqrt(dx*dx+dy*dy)
            y = y0 + dl*dy/np.sqrt(dx*dx+dy*dy)
            theta = np.rad2deg(np.arctan2(-dy, dx)) % 360
        elif self.features[f][0] == 'loop':
            x0, y0, d = self.features[f][1:]
            if dl < d/2:
                x = x0+dl
                y = y0
                theta = 0
            elif dl > d*np.pi+d/2:
                x = x0+dl+d/2
                y = y0
                theta = 0
            else:
                theta = (dl-d/2)*2/d
                dx = d*np.cos(theta)/2
                dy = d*np.sin(theta)/2
                theta = np.rad2deg(theta)
                x = x0 + dx + d/2
                y = y0 + dy + d/2
        else:
            x, y, theta = 0, 0, 0
        return x, y, theta

    def getPlayerPoint(self, l):
        if self.space and l >= len(self.segments)-1:
            dl = l - (len(self.segments)-1)
            x0, y0, theta0 = self.segments[-2]
            x1, y1, theta1 = self.segments[-1]
            x = x1 + dl*(x1-x0)
            y = y1 + dl*(y1-y0)
            return x, y, theta1
        x0, y0, theta = self.segments[int(l)]        
        if l >= len(self.segments)-1:
            x1, y1, theta1 = self.segments[0]
            x1 += self.x_total
        else:
            x1, y1, theta1 = self.segments[int(l+1)]
        dl = l - int(l)
        x = x0 + dl*(x1-x0)
        y = y0 + dl*(y1-y0)
        return x, y, theta

    def overlap(self, track, l, same=False):
        x, y, theta = self.segments[int(l+1) % len(self.segments)]
        f_all = np.where((track.x_seg >= x-.5) * (track.x_seg <= x +.5))[0]
        for f in f_all:
            x1, y1, theta1 = track.segments[f]
            dtheta = abs((theta1-theta+180) % 360 - 180)
            if same and (abs(l-f) <= OVERLAP_DIST+1) or abs(l-f)>self.x_total-OVERLAP_DIST-1:
                continue
            if (x1-x)*(x1-x)+(y1-y)*(y1-y) < OVERLAP_DIST*OVERLAP_DIST and dtheta < 90:
                return (True, f)
        return (False, l)


    def collide(self, l1, l2):
        x, y, theta = self.segments[int(l1+1) % len(self.segments)]
        f_all = np.where((self.x_seg >= x-.5) * (self.x_seg <= x +.5))[0]
        x1, y1, theta1 = self.segments[int(l2)]
        dtheta = abs((theta1-theta+180) % 360 - 180)
        return (x1-x)*(x1-x)+(y1-y)*(y1-y) < OVERLAP_DIST*OVERLAP_DIST and dtheta < 90