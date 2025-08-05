#define _WIN32_WINNT 0x0600

#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>   // For Sleep()
#include <iostream>
#include <string>

#pragma comment(lib, "ws2_32.lib")

int main() {
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "WSAStartup failed\n";
        system("pause");
        return 1;
    }

    std::string ip;
    int port;

    std::cout << "Enter the server IP: ";
    std::cin >> ip;

    std::cout << "Enter the port: ";
    std::cin >> port;

    SOCKET clientSocket = INVALID_SOCKET;
    sockaddr_in serverAddr{};
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(port);
    serverAddr.sin_addr.s_addr = inet_addr(ip.c_str());

    if (serverAddr.sin_addr.s_addr == INADDR_NONE) {
        std::cerr << "Invalid IP address\n";
        WSACleanup();
        system("pause");
        return 1;
    }

    std::cout << "Trying to connect to " << ip << ":" << port << "...\n";

    while (true) {
        clientSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (clientSocket == INVALID_SOCKET) {
            std::cerr << "Error creating socket: " << WSAGetLastError() << "\n";
            WSACleanup();
            system("pause");
            return 1;
        }

        if (connect(clientSocket, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
            std::cerr << "Connection failed: " << WSAGetLastError() << ". Retrying in 3 seconds...\n";
            closesocket(clientSocket);
            Sleep(3000);
        } else {
            std::cout << "[Connected to server]\n";
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
                std::cerr << "Error sending data: " << WSAGetLastError() << "\n";
                break;
            }

            char buffer[1024];
            int bytesReceived = recv(clientSocket, buffer, sizeof(buffer) - 1, 0);
            if (bytesReceived > 0) {
                buffer[bytesReceived] = '\0';
                std::cout << "[Server]: " << buffer << "\n";
            } else if (bytesReceived == 0) {
                std::cout << "[Server disconnected]\n";
                break;
            } else {
                std::cerr << "Error receiving data: " << WSAGetLastError() << "\n";
                break;
            }
        } else {
            std::cout << "[Invalid command - use 0, 1 or exit]\n";
        }
    }

    closesocket(clientSocket);
    WSACleanup();

    std::cout << "Press Enter to exit...";
    std::cin.ignore();
    std::cin.get();

    return 0;
}
