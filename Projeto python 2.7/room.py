import threading
import time
from socket import *


class CheckADM(threading.Thread):  # Esta thread é executada por todos os membros da sala, menos o adm. Ela checa se o adm se desconectou
    def __init__(self, room, myNick, client):
        threading.Thread.__init__(self)
        self.room = room
        self.members = room.members
        self.myNick = myNick
        self.client = client

    def run(self):
        """Checa continuamente se o adm está conectado, caso ele seja desconectado, roda o método changeADM"""
        check = True
        while check:
            if not self.client.running or self.client.banned:
                break
            time.sleep(2)
            try:
                socket_ = socket(AF_INET, SOCK_STREAM)
                hostADM, portADM = self.members[self.room.nickADM]
                socket_.connect((hostADM, int(portADM)))
                socket_.sendall(str(int(1)).encode())
                socket_.close()
            except:
                check = False
                self.changeADM()

    def changeADM(self):
        """Neste método, o adm atual é trocado pelo primeiro membro da lista 'self.room.queueADM', então todos os membros saberão quem será o novo adm"""
        try:  # Remover o atual adm está no try, pois caso o adm tenha saído da sala avisando a todos, ele já foi removido. Porém se ele saiu sem avisar, é necessário removê-lo
            ipADM = self.members[self.room.nickADM][0]
            portADM = self.members[self.room.nickADM][1]
            self.members.pop(self.room.nickADM)
            self.room.ips.pop((ipADM, portADM))
        except:
            pass

        newADM = self.room.queueADM.pop(0)  # O novo adm é o primeiro membro da fila self.room.queueADM
        self.room.nickADM = newADM
        self.room.ipADM = self.members[newADM][0]
        self.room.portADM = self.members[newADM][1]
        print('O dono da sala se desconectou!!!')
        if not self.myNick == newADM:  # Se o novo adm não for este próprio cliente, então ele voltará a rodar a thread de checagem de adm
            print(f'{newADM} é o novo dono da sala!!')
            self.run()
        else:  # Caso o novo adm seja este próprio cliente, agora ele não rodará mais esta thread e passará a fazer a checagem dos membros
            print('-'*30 + '\nVocê é o novo dono da sala!!\n' + '-'*30)
            print(f'\nA sala agora está no seu endereço:\nIP: {self.client.ip}\nPorta: {self.client.port}')
            print('\nComandos administrativos:'
                  '\n/ban nick    -> Para banir um membro da sala'
                  '\n/kick nick   -> Para expulsar um membro da sala\n')
            self.client.adm = True
            chekingMembers = CheckMembers(self.room, self.client)
            chekingMembers.start()

class CheckMembers(threading.Thread):  # Esta thread é executada somente pelo adm, na qual ele checa continuamente se algum membro se desconectou
    def __init__(self, room, client):
        threading.Thread.__init__(self)
        self.room = room
        self.client = client

    def run(self):
        """Checa continuamente se algum membro foi desconectado da sala. Caso encontre, envia esta informação para toda a sala"""
        while True:
            time.sleep(0.1)
            if not self.client.running or self.client.banned:
                break
            for member in self.room.queueADM:
                if not self.client.running or self.client.banned:
                    break
                time.sleep(0.1)
                try:
                    hostMember, portMember = self.room.members[member]
                    socket_ = socket(AF_INET, SOCK_STREAM)
                    socket_.connect((hostMember, portMember))
                    socket_.sendall(str(int(60456)).encode())
                except:
                    self.memberDisconnect(member)
                    time.sleep(0.5)

    def memberDisconnect(self, member):
        """Remove o membro desconectado da sala e envia um update de sala para todos os membros"""
        try:
            ipMember, portMember = self.room.members[member]
            self.room.members.pop(member)
            self.room.ips.pop((ipMember, portMember))
            self.room.queueADM.remove(member)
            print(f'O usuário {member} foi desconectado')
            self.client.updateRoom('Disconnected', member, ipMember, portMember)
        except:
            pass







class Room():
    def __init__(self, roomName, nickADM, ipADM, portADM, queueADM=[], members={}, ips={}, ban=[]):
        self.roomName = roomName  # Nome da sala
        self.nickADM = nickADM  # Nick do adm da sala
        self.ipADM = ipADM  # Ip do adm da sala
        self.portADM = portADM  # Porta do adm da sala
        self.queueADM = queueADM  # Esta lista representa uma fila de membros, caso o adm seja desconectado, o primeiro da fila vira adm
        self.members = members if members != {} else {nickADM: (ipADM, portADM)}  # Dicionário com membros da sala -> nick: (ip,porta)
        self.ips = ips if ips != {} else {(ipADM,portADM): nickADM}  # Dicionário com membros da sala -> (ip,porta): nick
        self.ban = ban  # Lista de pessoas banidas da sala