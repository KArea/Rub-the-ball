import pygame
import sys
import traceback
from pygame.locals import *
from random import *


# 球类继承自Spirte类
class Ball(pygame.sprite.Sprite):
    def __init__(self, grayball_image, greenball_image, position, speed, bg_size, target):
        # 初始化动画精灵
        pygame.sprite.Sprite.__init__(self)

        self.grayball_image = pygame.image.load(grayball_image).convert_alpha()         #加载为透明图片
        self.greenball_image = pygame.image.load(greenball_image).convert_alpha()
        self.rect = self.grayball_image.get_rect()                                      #获得位置矩形
        self.rect.left, self.rect.top = position                                        #小球放在指定位置
        self.side = [choice([-1, 1]), choice([-1, 1])]                                  #取随机方向
        self.speed = speed                                                              #获得速度
        self.collide = False                                                            #设定碰撞参数
        self.target = target                                                            #设置小球摩擦属性，对应摩擦事件数量
        self.control = False                                                            #设定控制参数
        self.width, self.height = bg_size[0], bg_size[1]                                #设定窗口尺寸
        self.radius = self.rect.width / 2                                               #设定半径参数

    def move(self):
        if self.control:                                                        #如果被控制，按speed移动
            self.rect = self.rect.move(self.speed)
        else:                                                                   #如果未被控制，当前速度与方向相乘
            self.rect = self.rect.move((self.side[0] * self.speed[0], \
                                        self.side[1] * self.speed[1]))

        # 如果小球的左侧出了边界，那么将小球左侧的位置改为右侧的边界
        # 这样便实现了从左边进入，右边出来的效果
        if self.rect.right <= 0:                            #若小球右边界在屏幕左边界的左侧，小球左边界重新赋值至屏幕右边界
            self.rect.left = self.width

        elif self.rect.left >= self.width:
            self.rect.right = 0

        elif self.rect.bottom <= 0:
            self.rect.top = self.height

        elif self.rect.top >= self.height:
            self.rect.bottom = 0

    def check(self, motion):
        if self.target < motion < self.target + 5:          #检查motion变量数值是否在小球摩擦属性范围内
            return True
        else:
            return False


class Glass(pygame.sprite.Sprite):
    def __init__(self, glass_image, mouse_image, bg_size):
        # 初始化动画精灵
        pygame.sprite.Sprite.__init__(self)

        self.glass_image = pygame.image.load(glass_image).convert_alpha()
        self.glass_rect = self.glass_image.get_rect()
        self.glass_rect.left, self.glass_rect.top = \
            (bg_size[0] - self.glass_rect.width) // 2, \
            bg_size[1] - self.glass_rect.height

        self.mouse_image = pygame.image.load(mouse_image).convert_alpha()
        self.mouse_rect = self.mouse_image.get_rect()
        self.mouse_rect.left, self.mouse_rect.top = \
            self.glass_rect.left, self.glass_rect.top
        pygame.mouse.set_visible(False)                         #设置鼠标为不可见


def main():
    pygame.init()

    grayball_image = "gray_ball.png"
    greenball_image = "green_ball.png"
    glass_image = "glass.png"
    mouse_image = "hand.png"
    bg_image = "background.png"

    running = True

    # 添加魔性的背景音乐
    pygame.mixer.music.load("bg_music.ogg")
    pygame.mixer.music.play()

    # 添加音效
    loser_sound = pygame.mixer.Sound("loser.wav")
    laugh_sound = pygame.mixer.Sound("laugh.wav")
    winner_sound = pygame.mixer.Sound("winner.wav")
    hole_sound = pygame.mixer.Sound("hole.wav")

    # 音乐播放完时游戏结束
    GAMEOVER = USEREVENT                            #自定义事件，"USEREVENT","USEREVENT + 1"...
    pygame.mixer.music.set_endevent(GAMEOVER)       #获取背景音乐播放结束的事件消息

    # 根据背景图片指定游戏界面尺寸
    bg_size = width, height = 1024, 681
    screen = pygame.display.set_mode(bg_size)
    pygame.display.set_caption("Play the ball - FishC Demo")

    background = pygame.image.load(bg_image).convert_alpha()

    # 5 个坑的范围，因为 100% 命中太难，所以只要在范围内即可
    # 每个元素：(x1, x2, y1, y2)
    hole = [(117, 119, 199, 201), (225, 227, 390, 392), \
            (503, 505, 320, 322), (698, 700, 192, 194), \
            (906, 908, 419, 421)]

    # 存放要打印的消息
    msgs = []

    # 用来存放小球对象的列表
    balls = []

    #生成一个组，放入创建的球并用来检测碰撞
    group = pygame.sprite.Group()

    # 创建 5 个小球
    for i in range(5):
        # 位置随机，速度随机
        position = randint(0, width - 100), randint(0, height - 100)
        speed = [randint(1, 10), randint(1, 10)]
        ball = Ball(grayball_image, greenball_image, position, speed, bg_size, 5 * (i + 1))
        # 检测新诞生的球是否会卡住其他球
        while pygame.sprite.spritecollide(ball, group, False, pygame.sprite.collide_circle):
            ball.rect.left, ball.rect.top = randint(0, width - 100), randint(0, height - 100)
        balls.append(ball)
        group.add(ball)

    # 生成摩擦摩擦的玻璃面板
    glass = Glass(glass_image, mouse_image, bg_size)

    # motion 记录鼠标在玻璃面板产生的事件数量
    motion = 0

    # 1 秒检查 1 次鼠标摩擦摩擦产生的事件数量
    MYTIMER = USEREVENT + 1
    pygame.time.set_timer(MYTIMER, 1000)

    # 设置持续按下键盘的重复响应set_repeat（delay，interval）
    pygame.key.set_repeat(100, 100)

    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            #退出事件
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            # 游戏失败
            elif event.type == GAMEOVER:            #GAMEOVER事件，由set_endevent()函数提供，bgm结束时触发
                loser_sound.play()
                pygame.time.delay(2000)
                laugh_sound.play()
                running = False

            # 1 秒检查 1 次鼠标摩擦摩擦产生的事件数量
            elif event.type == MYTIMER:             #MYTIMER事件，计时一秒触发
                if motion:
                    for each in group:
                        if each.check(motion):
                            each.speed = [0, 0]
                            each.control = True
                    motion = 0

            elif event.type == MOUSEMOTION:         #记录鼠标摩擦次数
                motion += 1

            # 当小球的 control 属性为 True 时
            # 可是使用按键 w、s、a、d 分别上、下、左、右移动小球
            # 带加速度的哦^_^
            elif event.type == KEYDOWN:             #此处加速度的实现依赖set_repeat()函数的设置
                if event.key == K_w:                #检测w键按下
                    for each in group:              #迭代group中小球
                        if each.control:            #检测小球的control属性
                            each.speed[1] -= 1      #每次速度减1

                if event.key == K_s:
                    for each in group:
                        if each.control:
                            each.speed[1] += 1

                if event.key == K_a:
                    for each in group:
                        if each.control:
                            each.speed[0] -= 1

                if event.key == K_d:
                    for each in group:
                        if each.control:
                            each.speed[0] += 1

                if event.key == K_SPACE:
                    # 判断小球是否在坑内
                    for each in group:
                        if each.control:
                            for i in hole:                                              #迭代hole列表中的洞并检测小球是否在洞中
                                if i[0] <= each.rect.left <= i[1] and \
                                                        i[2] <= each.rect.top <= i[3]:
                                    # 播放音效
                                    hole_sound.play()
                                    each.speed = [0, 0]
                                    # 从 group 中移出，这样其他球就会忽视它
                                    group.remove(each)
                                    # 放到 balls 列表中的最前，也就是第一个绘制的球
                                    # 这样当球在坑里时，其它球会从它上边过去，而不是下边
                                    temp = balls.pop(balls.index(each))
                                    balls.insert(0, temp)
                                    # 一个坑一个球
                                    hole.remove(i)
                            # 坑都补完了，游戏结束
                            if not hole:
                                pygame.mixer.music.stop()
                                winner_sound.play()
                                pygame.time.delay(3000)
                                # 打印“然并卵”
                                msg = pygame.image.load("win.png").convert_alpha()
                                msg_pos = (width - msg.get_width()) // 2, \
                                          (height - msg.get_height()) // 2
                                msgs.append((msg, msg_pos))
                                laugh_sound.play()
        #绘制背景和玻璃面板
        screen.blit(background, (0, 0))
        screen.blit(glass.glass_image, glass.glass_rect)

        # 限制鼠标只能在玻璃内摩擦摩擦
        glass.mouse_rect.left, glass.mouse_rect.top = pygame.mouse.get_pos()            #获得鼠标位置并赋值给glass.mouse
        if glass.mouse_rect.left < glass.glass_rect.left:
            glass.mouse_rect.left = glass.glass_rect.left
        if glass.mouse_rect.left > glass.glass_rect.right - glass.mouse_rect.width:
            glass.mouse_rect.left = glass.glass_rect.right - glass.mouse_rect.width
        if glass.mouse_rect.top < glass.glass_rect.top:
            glass.mouse_rect.top = glass.glass_rect.top
        if glass.mouse_rect.top > glass.glass_rect.bottom - glass.mouse_rect.height:
            glass.mouse_rect.top = glass.glass_rect.bottom - glass.mouse_rect.height

        #绘制自定义鼠标
        screen.blit(glass.mouse_image, glass.mouse_rect)

        for each in balls:
            each.move()
            if each.collide:                                        #如果碰撞，赋给小球随机速度并设置collide属性为False
                each.speed = [randint(1, 10), randint(1, 10)]
                each.collide = False
            if each.control:                                        #如果被控制，绘制绿色小球，否则绘制灰色小球
                screen.blit(each.greenball_image, each.rect)
            else:
                screen.blit(each.grayball_image, each.rect)

        for each in group:
            # 先从组中移出当前球，检测碰撞并修改该球的collide和control属性，然后将球放回group
            group.remove(each)
            # 判断当前球与其他球是否相撞
            if pygame.sprite.spritecollide(each, group, False, pygame.sprite.collide_circle):
                each.side[0] = -each.side[0]
                each.side[1] = -each.side[1]
                each.collide = True                 #检测碰撞的小球的collide属性设定为True
                if each.control:                    #受控的小球如果碰撞，就将速度方向取反并设定为失控
                    each.side[0] = -1
                    each.side[1] = -1
                    each.control = False
            # 将当前球添加回组中
            group.add(each)

        for msg in msgs:
            screen.blit(msg[0], msg[1])

        pygame.display.flip()       #刷新屏幕
        clock.tick(30)              #设定30帧


if __name__ == "__main__":
    # 这样做的好处是双击打开时如果出现异常可以报告异常，而不是一闪而过！
    try:
        main()
    except SystemExit:              #正常退出什么也不做
        pass
    except:
        traceback.print_exc()       #追踪异常，需要traceback模块
        pygame.quit()
        input()



