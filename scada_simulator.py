import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import pygame
import os

class SCADASimulator:
    def __init__(self, root):
        pygame.mixer.init()
        self.root = root
        self.root.title("SCADA Simulador")
        self.root.geometry("500x500")
        self.passo = 0
        self.emergencia = False
        self.estado = {}
        self.load_resources()
        self.build_ui()
        self.update_ui()

    def load_resources(self):
        R = {}
        path = os.path.join(os.path.dirname(__file__), 'resources')
        R['led_on'] = ImageTk.PhotoImage(Image.open(os.path.join(path,'led_on.png')))
        R['led_off'] = ImageTk.PhotoImage(Image.open(os.path.join(path,'led_off.png')))
        R['valve_open'] = ImageTk.PhotoImage(Image.open(os.path.join(path,'valve_open.png')))
        R['valve_closed'] = ImageTk.PhotoImage(Image.open(os.path.join(path,'valve_closed.png')))
        R['tank'] = ImageTk.PhotoImage(Image.open(os.path.join(path,'tank.png')))
        self.R = R
        self.sound_alarm = pygame.mixer.Sound(os.path.join(path,'sound_alarm.wav'))
        self.sound_valve = pygame.mixer.Sound(os.path.join(path,'sound_valve.wav'))

    def build_ui(self):
        tk.Label(self.root, image=self.R['tank']).pack(pady=10)
        self.frames = {}
        for var in ['nivel_baixo','nivel_alto','valvula_entrada','valvula_saida','emergencia']:
            f = tk.Frame(self.root)
            f.pack(pady=5)
            tk.Label(f, text=var.replace('_',' ').title()+':', width=20, anchor='e').pack(side='left')
            lbl = tk.Label(f)
            lbl.pack(side='left')
            self.frames[var] = lbl
        tk.Button(self.root, text="▶ Próximo", command=self.proximo_pass).pack(pady=10)
        tk.Button(self.root, text="⚠ Emergência", command=self.ativar_emergencia).pack()
        tk.Button(self.root, text="🔄 Reiniciar", command=self.reiniciar).pack(pady=10)

    def update_ui(self):
        st = self.estado
        self.frames['nivel_baixo'].config(image=self.R['led_on'] if st.get('nivel_baixo') else self.R['led_off'])
        self.frames['nivel_alto'].config(image=self.R['led_on'] if st.get('nivel_alto') else self.R['led_off'])
        self.frames['valvula_entrada'].config(image=self.R['valve_open'] if st.get('valvula_entrada') else self.R['valve_closed'])
        self.frames['valvula_saida'].config(image=self.R['valve_open'] if st.get('valvula_saida') else self.R['valve_closed'])
        self.frames['emergencia'].config(image=self.R['led_on'] if st.get('emergencia') else self.R['led_off'])

    def proximo_pass(self):
        if self.emergencia:
            messagebox.showwarning("!", "Emergência ativada!")
            return
        st = {k:False for k in ['nivel_baixo','nivel_alto','valvula_entrada','valvula_saida','emergencia']}
        if self.passo == 0:
            st['nivel_baixo'], st['valvula_entrada'] = True, True
            self.sound_valve.play()
        elif self.passo == 1:
            st['nivel_baixo'], st['valvula_entrada'] = True, True
        elif self.passo == 2:
            st['nivel_alto'] = True
        elif self.passo == 3:
            st['nivel_alto'], st['valvula_saida'] = True, True
            self.sound_valve.play()
        elif self.passo == 4:
            st['nivel_baixo'] = True
        else:
            self.passo = -1
        self.estado = st
        self.passo += 1
        self.update_ui()

    def ativar_emergencia(self):
        self.emergencia = True
        self.estado = {k:False for k in ['nivel_baixo','nivel_alto','valvula_entrada','valvula_saida']}
        self.estado['emergencia'] = True
        self.sound_alarm.play()
        self.update_ui()

    def reiniciar(self):
        self.emergencia = False
        self.passo = 0
        self.estado = {k:False for k in ['nivel_baixo','nivel_alto','valvula_entrada','valvula_saida','emergencia']}
        self.update_ui()

if __name__ == '__main__':
    root = tk.Tk()
    app = SCADASimulator(root)
    app.estado = {k:False for k in ['nivel_baixo','nivel_alto','valvula_entrada','valvula_saida','emergencia']}
    root.mainloop()