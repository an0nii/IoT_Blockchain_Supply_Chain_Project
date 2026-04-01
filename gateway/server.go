package main

import (
	"crypto/x509"
	"fmt"
	"log"
	"net/http"
	"os"
	"path"
	"time"

	"github.com/hyperledger/fabric-gateway/pkg/client"
	"github.com/hyperledger/fabric-gateway/pkg/hash"
	"github.com/hyperledger/fabric-gateway/pkg/identity"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
)

type deviceEntry struct {
	deviceID string
	gateway  *client.Gateway
}

type Server struct {
	cfg          Config
	grpcConn     *grpc.ClientConn
	adminGateway *client.Gateway
	devices      map[string]*deviceEntry
	mux          *http.ServeMux
}

func newServer(cfg Config) (*Server, error) {
	grpcConn, err := newGRPCConnection(cfg.TLSCertPath, cfg.PeerEndpoint, cfg.GatewayPeer)
	if err != nil {
		return nil, fmt.Errorf("grpc: %w", err)
	}

	adminGW, err := connectGateway(grpcConn, cfg.AdminMSPID, cfg.AdminCertPath, cfg.AdminKeyPath)
	if err != nil {
		grpcConn.Close()
		return nil, fmt.Errorf("admin gateway: %w", err)
	}

	devicesMap := make(map[string]*deviceEntry)
	deviceConfigs, err := loadDevices(cfg.DevicesFile)
	if err != nil {
		log.Printf("Warning: could not load devices file (%s): %v", cfg.DevicesFile, err)
	} else {
		for _, dc := range deviceConfigs {
			gw, err := connectGateway(grpcConn, dc.MSPID, dc.CertPath, dc.KeyPath)
			if err != nil {
				log.Printf("Warning: skipping device %s: %v", dc.DeviceID, err)
				continue
			}
			devicesMap[dc.APIKey] = &deviceEntry{
				deviceID: dc.DeviceID,
				gateway:  gw,
			}
			log.Printf("Loaded device: %s", dc.DeviceID)
		}
	}

	s := &Server{
		cfg:          cfg,
		grpcConn:     grpcConn,
		adminGateway: adminGW,
		devices:      devicesMap,
		mux:          http.NewServeMux(),
	}
	s.routes()
	return s, nil
}

func (s *Server) serve() error {
	return http.ListenAndServe(s.cfg.ListenAddr, corsMiddleware(s.mux))
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, X-Admin-Key, X-Device-Key")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func (s *Server) close() {
	s.adminGateway.Close()
	for _, d := range s.devices {
		d.gateway.Close()
	}
	s.grpcConn.Close()
}

func (s *Server) contract(gw *client.Gateway) *client.Contract {
	return gw.GetNetwork(s.cfg.ChannelName).GetContract(s.cfg.ChaincodeName)
}

func newGRPCConnection(tlsCertPath, peerEndpoint, gatewayPeer string) (*grpc.ClientConn, error) {
	cert, err := loadCertificate(tlsCertPath)
	if err != nil {
		return nil, fmt.Errorf("load TLS cert: %w", err)
	}
	certPool := x509.NewCertPool()
	certPool.AddCert(cert)

	conn, err := grpc.NewClient(
		peerEndpoint,
		grpc.WithTransportCredentials(credentials.NewClientTLSFromCert(certPool, gatewayPeer)),
	)
	if err != nil {
		return nil, fmt.Errorf("grpc.NewClient: %w", err)
	}
	return conn, nil
}

func connectGateway(conn *grpc.ClientConn, mspID, certPath, keyPath string) (*client.Gateway, error) {
	cert, err := loadCertificate(certPath)
	if err != nil {
		return nil, fmt.Errorf("load identity cert: %w", err)
	}
	id, err := identity.NewX509Identity(mspID, cert)
	if err != nil {
		return nil, err
	}

	keyPEM, err := readKeyFile(keyPath)
	if err != nil {
		return nil, err
	}
	privateKey, err := identity.PrivateKeyFromPEM(keyPEM)
	if err != nil {
		return nil, fmt.Errorf("parse private key: %w", err)
	}
	sign, err := identity.NewPrivateKeySign(privateKey)
	if err != nil {
		return nil, err
	}

	return client.Connect(
		id,
		client.WithSign(sign),
		client.WithHash(hash.SHA256),
		client.WithClientConnection(conn),
		client.WithEvaluateTimeout(5*time.Second),
		client.WithEndorseTimeout(15*time.Second),
		client.WithSubmitTimeout(5*time.Second),
		client.WithCommitStatusTimeout(time.Minute),
	)
}

func readKeyFile(keyPath string) ([]byte, error) {
	info, err := os.Stat(keyPath)
	if err != nil {
		return nil, fmt.Errorf("key path stat: %w", err)
	}
	if !info.IsDir() {
		return os.ReadFile(keyPath)
	}
	entries, err := os.ReadDir(keyPath)
	if err != nil {
		return nil, fmt.Errorf("read key dir: %w", err)
	}
	if len(entries) == 0 {
		return nil, fmt.Errorf("no key files in directory: %s", keyPath)
	}
	return os.ReadFile(path.Join(keyPath, entries[0].Name()))
}

func loadCertificate(filePath string) (*x509.Certificate, error) {
	pem, err := os.ReadFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("read cert file: %w", err)
	}
	return identity.CertificateFromPEM(pem)
}
