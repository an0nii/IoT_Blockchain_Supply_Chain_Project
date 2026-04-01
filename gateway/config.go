package main

import (
	"encoding/json"
	"fmt"
	"os"
)

type Config struct {
	ListenAddr    string
	ChannelName   string
	ChaincodeName string
	PeerEndpoint  string
	GatewayPeer   string
	TLSCertPath   string
	AdminAPIKey   string
	AdminMSPID    string
	AdminCertPath string
	AdminKeyPath  string
	DevicesFile   string
}

type DeviceConfig struct {
	APIKey   string `json:"apiKey"`
	DeviceID string `json:"deviceId"`
	MSPID    string `json:"mspId"`
	CertPath string `json:"certPath"`
	KeyPath  string `json:"keyPath"`
}

func loadConfig() Config {
	return Config{
		ListenAddr:    getEnv("GATEWAY_ADDR", ":3000"),
		ChannelName:   getEnv("FABRIC_CHANNEL", "mychannel"),
		ChaincodeName: getEnv("FABRIC_CHAINCODE", "iot-supply-chain"),
		PeerEndpoint:  getEnv("FABRIC_PEER_ENDPOINT", "dns:///localhost:7051"),
		GatewayPeer:   getEnv("FABRIC_GATEWAY_PEER", "peer0.org1.example.com"),
		TLSCertPath:   mustEnv("FABRIC_TLS_CERT_PATH"),
		AdminAPIKey:   mustEnv("ADMIN_API_KEY"),
		AdminMSPID:    getEnv("ADMIN_MSP_ID", "Org1MSP"),
		AdminCertPath: mustEnv("ADMIN_CERT_PATH"),
		AdminKeyPath:  mustEnv("ADMIN_KEY_PATH"),
		DevicesFile:   getEnv("DEVICES_CONFIG", "devices.json"),
	}
}

func loadDevices(filePath string) ([]DeviceConfig, error) {
	data, err := os.ReadFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("read devices file: %w", err)
	}
	var devices []DeviceConfig
	if err := json.Unmarshal(data, &devices); err != nil {
		return nil, fmt.Errorf("parse devices file: %w", err)
	}
	return devices, nil
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func mustEnv(key string) string {
	v := os.Getenv(key)
	if v == "" {
		panic("required environment variable not set: " + key)
	}
	return v
}
