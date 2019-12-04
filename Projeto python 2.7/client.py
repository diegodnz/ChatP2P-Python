from socket import *
import time

def splitMessage(message):
    """Recebe uma string com informacoes separadas por \n e devolve uma lista, separando as informacoes"""
    listInformations = []
    string = ''
    for chr in message:
        if chr != '\n':
            string += chr
        else:
            listInformations.append(string)
            string = ''
    return listInformations

class Client():
    def __init__(self, nick, ip, port, adm, room):
        self.nick = nick
        self.ip = ip
        self.port = port
        self.room = room
        self.reqEntry = False  # Este atributo indice se outra thread requisitou raw_input
        self.reqMessage = ''  # Texto que pede ao usuario o raw_input requisitado
        self.entry = ''  # Indica o raw_input requisitado
        self.adm = adm  # Indica se e adm da sala (bool)
        self.running = True  # Indica se o peer esta na sala, ou seja, nao foi removido ou saiu
        self.banned = False  # Indica se o peer foi banido


    def sendText(self, text, dic, blackList=[]):
        """Recebe um texto e um dicionario contendo pessoas. Envia o texto para cada pessoa do dicionario"""
        for person in dic:
            if person not in blackList:  # blackList indica as pessoas na qual nao se deve mandar a mensagem
                host, port = dic[person][0], dic[person][1]
                socket_ = socket(AF_INET, SOCK_STREAM)
                socket_.connect((host, port))
                socket_.sendall(str(self.port).encode())
                time.sleep(0.02)
                socket_.sendall(('text\n' + str(text) + '\n').encode())  # Indica que vai mandar uma mensagem
                time.sleep(0.05)


    def chatPeer(self):
        """Chat dentro de uma sala. Funciona tanto para um membro, quanto para um adm"""
        print('\nSiga as instrucoes:'
              '\n/all msg     -> Para enviar uma mensagem para toda a sala'
              '\n/w nick msg  -> Para enviar uma mensagem privada para algum membro'
              '\n/members     -> Para visualizar a lista de integrantes da sala'
              '\n/sair        -> Para sair da sala\n')
        if self.adm:
            print('Comandos administrativos:'
                  '\n/ban nick    -> Para banir um membro da sala'
                  '\n/kick nick   -> Para expulsar um membro da sala\n')
        while self.running and not self.banned:
            entry = raw_input('')
            if self.running and not self.banned:
                if entry[0:4] == '/all':
                    self.sendText(entry[5:], self.room.members, [self.nick])
                    print('Voce: ' + str(entry[5:]))
                elif entry[0:2] == '/w':
                    nick = ''
                    indexMsg = 3
                    for chr in entry[3:]:
                        indexMsg += 1
                        if chr != ' ':
                            nick += chr
                        else:
                            break
                    msg = entry[indexMsg:]
                    if msg and nick in self.room.members and nick != self.nick:
                        ip = self.room.members[nick][0]
                        port = self.room.members[nick][1]
                        self.sendText('(PRIVADO) ' + msg, {nick:(ip, port)}, [self.nick])
                        print('Voce -> ' + str(nick) + ': ' + str(msg))
                    elif not msg:
                        print('Voce nao inseriu a mensagem')
                    elif nick == self.nick:
                        print('Voce nao pode mandar uma mensagem para si mesmo.')
                    else:
                        print('O usuario nao esta presente nesta sala')
                elif entry[0:9] == '/members':
                    print('\nMembros da sala:')
                    for member in self.room.members:
                        print(member)
                    print('\n')
                elif entry == '/sair':
                    self.room.members.pop(self.nick)
                    self.room.ips.pop((self.ip, self.port))
                    self.updateRoom('sair', self.nick, self.ip, self.port)
                    print('Voce saiu da sala.')
                    self.running = False
                elif self.adm and entry[0:4] == '/ban':
                    nick = entry[5:]
                    if nick in self.room.members and nick != self.nick:
                        ip = self.room.members[nick][0]
                        port = self.room.members[nick][1]
                        self.updateRoom('ban', nick, ip, port)
                        self.room.members.pop(nick)
                        self.room.ips.pop((ip, port))
                        self.room.ban.append((ip, port))
                        self.room.queueADM.remove(nick)
                        print('Voce baniu ' + str(nick) + '!!')
                    elif nick == self.nick:
                        print('Voce nao pode banir a si mesmo')
                    else:
                        print('Este membro nao esta no grupo')
                elif self.adm and entry[0:5] == '/kick':
                    nick = entry[6:]
                    if nick in self.room.members and nick != self.nick:
                        ip = self.room.members[nick][0]
                        port = self.room.members[nick][1]
                        self.updateRoom('remove', nick, ip, port)
                        self.room.members.pop(nick)
                        self.room.ips.pop((ip, port))
                        self.room.queueADM.remove(nick)
                        print('Voce removeu ' + str(nick) + '.')
                    elif nick == self.nick:
                        print('Voce nao pode expulsar a si mesmo da sala')
                    else:
                        print('Este membro nao esta no grupo')
                elif self.reqEntry:
                    self.entry = entry
                    self.reqEntry = False
                else:
                    print('Comando invalido!!')
                if self.reqEntry:
                    print(self.reqMessage)
        if self.banned:
            print('Voce foi banido desta sala!!')


    def updateRoom(self, type, nick, ip, port):
        """Manda atualizacoes da sala para todos os membros"""
        for person in self.room.members:
            if person != self.nick and not (type=='add' and nick == person):
                ipMember, portMember = self.room.members[person][0], self.room.members[person][1]
                socket_ = socket(AF_INET, SOCK_STREAM)
                socket_.connect((ipMember, portMember))
                socket_.sendall(str(self.port).encode())
                time.sleep(0.02)
                socket_.sendall(('update\n' + type + '\n' + nick + '\n' + ip + '\n' + str(port) + '\n').encode())
                time.sleep(0.05)
