package main

import (
	"log"
)

func main() {
	cfg := loadConfig()

	srv, err := newServer(cfg)
	if err != nil {
		log.Fatalf("failed to initialise gateway: %v", err)
	}
	defer srv.close()

	log.Printf("IoT Fabric Gateway listening on %s", cfg.ListenAddr)
	log.Printf("Channel: %s  Chaincode: %s", cfg.ChannelName, cfg.ChaincodeName)
	log.Printf("Devices loaded: %d", len(srv.devices))

	if err := srv.serve(); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
