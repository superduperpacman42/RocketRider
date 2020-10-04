import pygame
from PIL import Image
import os, sys, math, random
import numpy as np
from constants import *
from track import Track

exe = 0

class Game:

    def reset(self, respawn=False):
        ''' Resets the game '''
        self.tracks = []
        for i in range(2):
            self.tracks.append(Track(self, 120, -i*3))
        maxX = 0
        maxI = 0
        for i, track in enumerate(self.tracks):
            if track.x_total > maxX:
                maxX = int(track.x_total)
                maxI = i
        for i, track in enumerate(self.tracks):
            track.extendTrack(maxX - track.x_total)
        self.playerTrack = 0
        self.playerL = 1
        self.v = 0
        self.theta = 0
        self.score = 0
        self.victory = False
        self.splash = False
        self.starsX = random.sample(range(int(MAX_WIDTH)), 60)
        self.starsY = random.sample(range(int(MAX_WIDTH)), 60)
        self.highestTrack = 2
        self.coins = [random.sample(range(int((len(t.segments)-1))), 5) for t in self.tracks]
        self.enemies = [[] for i in range(len(self.tracks))]
        self.overlap_any = False
        self.t = 0
        self.origin = (MAX_WIDTH/2, MAX_WIDTH/2, 0)

    def ui(self):
        ''' Draws the user interface overlay '''
        caption = self.font.render("Score: "+str(int(self.score)), True, (255,255,255))
        self.screen.blit(caption, (SCALE/2,SCALE/2))
        if self.victory:
            caption = self.font3.render("Victory", True, (255,255,255))
            self.screen.blit(caption, (WIDTH/6,SCALE*4))
            caption = self.font.render("You have made it to space!", True, (255,255,255))
            self.screen.blit(caption, (WIDTH/9,SCALE*15))
            caption = self.font0.render("Press [Enter] to play again...", True, (255,255,255))
            self.screen.blit(caption, (WIDTH/6.5,SCALE*18))

    def update(self, dt, keys):
        ''' Updates the game by a timestep and redraws graphics '''
        # if dt>100:
        #     return
        if self.splash:
            self.screen.blit(self.splashImage, (0,0,WIDTH,HEIGHT))
            return
        self.t += dt
        x0, y0, theta0 = self.tracks[self.playerTrack].getPlayerPoint(self.playerL)
        if self.overlap_any:
            self.playerL += dt*SPEED*.5
        else:
            self.playerL += dt*self.v
        if self.tracks[self.playerTrack].space:
            if self.playerL > len(self.tracks[self.playerTrack].segments):
                self.victory = True
        elif self.playerL > len(self.tracks[self.playerTrack].segments):
            self.playerL -= len(self.tracks[self.playerTrack].segments)
        x, y, theta = self.tracks[self.playerTrack].getPlayerPoint(self.playerL)
        self.v = self.v + SPEED*(y-y0)*dt/100
        self.v = max(min(self.v, SPEED*2), SPEED*.75)
        dtheta = (theta - self.theta+180) % 360 - 180
        self.theta = (self.theta + dtheta/5) % 360

        # scoring and levelup
        for i, coin in enumerate(self.coins[self.playerTrack]):
            if coin > 0 and self.tracks[self.playerTrack].collide(self.playerL, coin):
                self.coins[self.playerTrack][i] *= -1
                self.score += 1
                self.playSound("Popcorn.wav")
        if self.score >= self.highestTrack*5-5:
            self.levelup()

        # cleanup old tracks
        if len(self.tracks) > 3 and not self.playerTrack == 0:
            self.tracks = self.tracks[1:]
            self.coins = self.coins[1:]
            self.enemies = self.enemies[1:]
            self.playerTrack -= 1
        for i, enemyTrack in enumerate(self.enemies):
            for j, enemy in enumerate(enemyTrack):
                self.enemies[i][j] -= dt*SPEED*.25
                self.enemies[i][j] %= len(self.tracks[i].segments)
                if i == self.playerTrack and self.tracks[self.playerTrack].collide(self.playerL, enemy):
                    print("Kaboom")


        # Graphics
        surface = pygame.Surface((MAX_WIDTH, MAX_WIDTH))
        self.origin = (x*SCALE, y*SCALE, self.theta)

        # sky changes
        dcolor = max(0, 1-(self.score/5)/10)
        surface.fill((dcolor*100,dcolor*170,dcolor*255))
        nstars = max(0, min(len(self.starsX),self.score-25))
        for x, y in zip(self.starsX[:nstars], self.starsY[:nstars]):
            pygame.draw.rect(surface, (255-dcolor*100,255-dcolor*100,255-dcolor*100), (x-2, y-2, 5, 5))
        pygame.draw.rect(surface, (40*dcolor,140*dcolor,50*dcolor), (0, int(MAX_WIDTH*(1-dcolor*.5)), MAX_WIDTH, int(MAX_WIDTH*.5)))

        self.overlap_any = False
        for i, track in enumerate(self.tracks):
            if i == self.playerTrack:
                continue
            else:
                overlap = self.tracks[self.playerTrack].overlap(track, self.playerL)[0]
                if overlap:
                    if track.space:
                        self.playerTrack = len(self.tracks)-1
                    self.overlap_any = True
                    track.draw(surface, self.origin, -1, 2, enemyLs=self.enemies[i], coinLs=self.coins[i])
                else:
                    track.draw(surface, self.origin, -1, 0, enemyLs=self.enemies[i], coinLs=self.coins[i])
        track = self.tracks[self.playerTrack]
        overlap = track.overlap(track, self.playerL, True)[0]
        if overlap:
            self.overlap_any = True
            track.draw(surface, self.origin, self.playerL, 2, enemyLs=self.enemies[i], coinLs=self.coins[self.playerTrack])
        else:
            track.draw(surface, self.origin, self.playerL, 1, enemyLs=self.enemies[i], coinLs=self.coins[self.playerTrack])
        surface = pygame.transform.rotate(surface, -self.origin[2])
        self.screen.blit(surface, (WIDTH/2-surface.get_width()/2-WIDTH/4,HEIGHT/2-surface.get_height()/2))
        self.ui()

    def keyPressed(self, key):
        ''' Respond to a key press event '''
        if key==pygame.K_SPACE:
            for i, track in enumerate(self.tracks):
                overlap = self.tracks[self.playerTrack].overlap(track, self.playerL, i == self.playerTrack)
                if overlap[0]:
                    self.playSound("Clunk.wav")
                    self.playerTrack = i
                    self.playerL = overlap[1]
                    # if self.playerTrack == len(self.tracks)-1:
                    return
        if key==pygame.K_RETURN:
            if self.splash:
                self.splash = False
            if self.victory:
                self.reset()

    def levelup(self):
        if self.score > 50:
            if self.tracks[-1].space:
                return
            track = Track(self, 100, -self.highestTrack*3, space=True)
            self.highestTrack += 1
            self.tracks.append(track)
            self.coins.append([])
            self.enemies.append([])
            return
        self.highestTrack += 1
        track = Track(self, 100, -self.highestTrack*3)
        track.extendTrack(self.tracks[0].x_total - track.x_total)
        self.tracks.append(track)
        self.coins.append(random.sample(range(int((len(track.segments)-1)/3)), 5))
        # if self.highestTrack % 2 == 1:
        #     self.enemies.append(random.sample(range(len(track.segments)-1), 1))
        # else:
        self.enemies.append([])
        print(self.highestTrack)

        

################################################################################
    
    def __init__(self, name):
        ''' Initialize the game '''
        pygame.init()
        os.environ['SDL_VIDEO_WINDOW_POS'] = '0, 30'
        pygame.display.set_caption(name)
        self.screen = pygame.display.set_mode([WIDTH, HEIGHT])
        # icon = self.loadImage("Icon.png", scale=1)
        # icon.set_colorkey((255,0,0))
        # pygame.display.set_icon(icon.convert_alpha())
        self.audio = {}
        self.playMusic("RocketRider.wav")
        self.playSound("Clunk.wav", False)
        self.playSound("Popcorn.wav", False)

        self.cars1 = [self.loadImage("Car1.png")]
        self.cars2 = [self.loadImage("Car2.png")]
        self.cars3 = [self.loadImage("Car3.png")]
        self.segmentImagesFront = [self.loadImage("TrackFront.png")]
        self.segmentImagesBack = [self.loadImage("TrackBack.png")]
        self.segmentImagesFront1 = [self.loadImage("TrackFront1.png")]
        self.segmentImagesFront2 = [self.loadImage("TrackFront2.png")]
        self.segmentImagesBack1 = [self.loadImage("TrackBack1.png")]
        self.splashImage = self.loadImage("Popcorn.png")
        self.popcorn = [self.loadImage("Popcorn.png")]

        self.angles = list(range(0, 360, ANG_STEP))
        for angle in self.angles[1:]:
            self.segmentImagesFront.append(pygame.transform.rotate(self.segmentImagesFront[0], angle))
            self.segmentImagesBack.append(pygame.transform.rotate(self.segmentImagesBack[0], angle))
            self.segmentImagesFront1.append(pygame.transform.rotate(self.segmentImagesFront1[0], angle))
            self.segmentImagesBack1.append(pygame.transform.rotate(self.segmentImagesBack1[0], angle))
            self.segmentImagesFront2.append(pygame.transform.rotate(self.segmentImagesFront2[0], angle))
            self.popcorn.append(pygame.transform.rotate(self.popcorn[0], angle))
            self.cars1.append(pygame.transform.rotate(self.cars1[0], angle))
            self.cars2.append(pygame.transform.rotate(self.cars2[0], angle))
            self.cars3.append(pygame.transform.rotate(self.cars3[0], angle))


        self.font = pygame.font.Font("font/LCD_Solid.ttf", FONT_SIZE)
        self.font2 = pygame.font.Font("font/LCD_Solid.ttf", FONT_SIZE*2)
        self.font3 = pygame.font.Font("font/LCD_Solid.ttf", FONT_SIZE*3)
        self.font0 = pygame.font.Font("font/LCD_Solid.ttf", int(FONT_SIZE*.75))

        self.reset()
        self.run()

    def run(self):
        ''' Iteratively call update '''
        clock = pygame.time.Clock()
        self.pause = False
        while not self.pause:
            for event in pygame.event.get():
                if event.type is pygame.KEYDOWN:
                    self.keyPressed(event.key)
                if event.type == pygame.QUIT:
                    pygame.display.quit()
                    sys.exit()
            dt = clock.tick(TIME_STEP)
            self.update(dt, pygame.key.get_pressed())
            pygame.display.update()
    
    def loadImage(self, name, number=1, scale=PIXEL_RATIO):
        ''' Loads an image or list of images '''
        if not hasattr(self, "images"):
            self.images = {}
        elif name in self.images:
            return self.images[name]
        if exe:
            path = os.path.join(os.path.dirname(sys.executable), 'images')
        else:
            path = os.path.join(os.path.dirname(__file__), 'images')
        if number==1:
            img = pygame.image.load(os.path.join(path, name))
            img = pygame.transform.scale(img, [scale*img.get_width(), scale*img.get_height()])
        else:
            img = []
            for i in range(number):
                key = name[:-4]+str(i)+name[-4:]
                img.append(pygame.image.load(os.path.join(path, key)))
                img[-1] = pygame.transform.scale(img[-1], [scale*img[-1].get_width(), scale*img[-1].get_height()])
        self.images[name] = img
        return img

    def playMusic(self, name):
        ''' Plays the given background track '''
        if exe:
            path = os.path.join(os.path.dirname(sys.executable), 'audio')
        else:
            path = os.path.join(os.path.dirname(__file__), 'audio')
        pygame.mixer.music.load(os.path.join(path, name))
        pygame.mixer.music.play(-1)
        
    def playSound(self, name, play=True):
        ''' Plays the given sound effect ''' 
        if name in self.audio:
            sound = self.audio[name]
        else:
            if exe:
                path = os.path.join(os.path.dirname(sys.executable), 'audio')
            else:
                path = os.path.join(os.path.dirname(__file__), 'audio')        
            sound = pygame.mixer.Sound(os.path.join(path, name))
            self.audio[name] = sound
        if play:
            sound.play()


if __name__ == '__main__':
    game = Game("Rocket Rider")
