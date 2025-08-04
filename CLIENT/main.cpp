#define _WIN32_WINNT 0x0600

#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>   // Para Sleep()
#include <iostream>
#include <string>

#pragma comment(lib, "ws2_32.lib")

int main() {
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "WSAStartup falhou\n";
        system("pause");
        return 1;
    }

    std::string ip;
    int port;

    std::cout << "Introduz o IP do servidor: ";
    std::cin >> ip;

    std::cout << "Introduz a porta: ";
    std::cin >> port;

    SOCKET clientSocket = INVALID_SOCKET;
    sockaddr_in serverAddr{};
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(port);
    serverAddr.sin_addr.s_addr = inet_addr(ip.c_str());

    if (serverAddr.sin_addr.s_addr == INADDR_NONE) {
        std::cerr << "Endereço IP inválido\n";
        WSACleanup();
        system("pause");
        return 1;
    }

    std::cout << "Tentando conectar a " << ip << ":" << port << "...\n";

    while (true) {
        clientSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (clientSocket == INVALID_SOCKET) {
            std::cerr << "Erro ao criar socket: " << WSAGetLastError() << "\n";
            WSACleanup();
            system("pause");
            return 1;
        }

        if (connect(clientSocket, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
            std::cerr << "Falha na conexão: " << WSAGetLastError() << ". Tentando novamente em 3 segundos...\n";
            closesocket(clientSocket);
            Sleep(3000);
        } else {
            std::cout << "[Conectado ao servidor]\n";
            break;
        }
    }

    while (true) {
        std::string input;
        std::cout << "> ";
        std::cin >> input;

        if (input == "exit") {
            break;
        }

        if (input == "0" || input == "1") {
            int sent = send(clientSocket, input.c_str(), (int)input.size(), 0);
            if (sent == SOCKET_ERROR) {
                std::cerr << "Erro ao enviar dados: " << WSAGetLastError() << "\n";
                break;
            }

            char buffer[1024];
            int bytesReceived = recv(clientSocket, buffer, sizeof(buffer) - 1, 0);
            if (bytesReceived > 0) {
                buffer[bytesReceived] = '\0';
                std::cout << "[Servidor]: " << buffer << "\n";
            } else if (bytesReceived == 0) {
                std::cout << "[Servidor desconectado]\n";
                break;
            } else {
                std::cerr << "Erro ao receber dados: " << WSAGetLastError() << "\n";
                break;
            }
        } else {
            std::cout << "[Comando inválido - usa 0, 1 ou exit]\n";
        }
    }

    closesocket(clientSocket);
    WSACleanup();

    std::cout << "Pressiona Enter para sair...";
    std::cin.ignore();
    std::cin.get();

    return 0;
}
