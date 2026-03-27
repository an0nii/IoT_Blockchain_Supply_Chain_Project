package main

import (
	"crypto/ecdsa"
	"crypto/rsa"
	"crypto/x509"
	"encoding/pem"
	"fmt"
	"os"
	"time"

	"github.com/hyperledger/fabric-gateway/pkg/client"
	"github.com/hyperledger/fabric-gateway/pkg/identity"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
)

type FabricConfig struct {
	MSPID           string
	PeerEndpoint    string
	PeerTLSCertPath string
	TLSServerName   string
	CertPath        string
	KeyPath         string
	Channel         string
	Chaincode       string
	HTTPPort        string
	EvaluateTimeout time.Duration
	EndorseTimeout  time.Duration
	SubmitTimeout   time.Duration
	CommitTimeout   time.Duration
}

func loadConfig() (FabricConfig, error) {
	cfg := FabricConfig{
		MSPID:           os.Getenv("FABRIC_MSP_ID"),
		PeerEndpoint:    os.Getenv("FABRIC_PEER_ENDPOINT"),
		PeerTLSCertPath: os.Getenv("FABRIC_PEER_TLS_CERT_PATH"),
		TLSServerName:   os.Getenv("FABRIC_TLS_SERVER_NAME"),
		CertPath:        os.Getenv("FABRIC_CERT_PATH"),
		KeyPath:         os.Getenv("FABRIC_KEY_PATH"),
		Channel:         os.Getenv("FABRIC_CHANNEL"),
		Chaincode:       os.Getenv("FABRIC_CHAINCODE"),
		HTTPPort:        os.Getenv("HTTP_PORT"),
		EvaluateTimeout: 5 * time.Second,
		EndorseTimeout:  15 * time.Second,
		SubmitTimeout:   5 * time.Second,
		CommitTimeout:   60 * time.Second,
	}
	if cfg.HTTPPort == "" {
		cfg.HTTPPort = "3001"
	}

	missing := []string{}
	if cfg.MSPID == "" {
		missing = append(missing, "FABRIC_MSP_ID")
	}
	if cfg.PeerEndpoint == "" {
		missing = append(missing, "FABRIC_PEER_ENDPOINT")
	}
	if cfg.PeerTLSCertPath == "" {
		missing = append(missing, "FABRIC_PEER_TLS_CERT_PATH")
	}
	if cfg.CertPath == "" {
		missing = append(missing, "FABRIC_CERT_PATH")
	}
	if cfg.KeyPath == "" {
		missing = append(missing, "FABRIC_KEY_PATH")
	}
	if cfg.Channel == "" {
		missing = append(missing, "FABRIC_CHANNEL")
	}
	if cfg.Chaincode == "" {
		missing = append(missing, "FABRIC_CHAINCODE")
	}
	if len(missing) > 0 {
		return cfg, fmt.Errorf("missing Fabric configuration: %v", missing)
	}

	return cfg, nil
}

func newGateway(cfg FabricConfig) (*client.Gateway, *grpc.ClientConn, error) {
	tlsCert, err := os.ReadFile(cfg.PeerTLSCertPath)
	if err != nil {
		return nil, nil, err
	}
	creds := credentials.NewClientTLSFromCert(certPoolFromPEM(tlsCert), cfg.TLSServerName)
	conn, err := grpc.Dial(cfg.PeerEndpoint, grpc.WithTransportCredentials(creds))
	if err != nil {
		return nil, nil, err
	}

	id, err := newIdentity(cfg)
	if err != nil {
		conn.Close()
		return nil, nil, err
	}

	signer, err := newSigner(cfg)
	if err != nil {
		conn.Close()
		return nil, nil, err
	}

	gw, err := client.Connect(
		id,
		client.WithSign(signer),
		client.WithClientConnection(conn),
		client.WithEvaluateTimeout(cfg.EvaluateTimeout),
		client.WithEndorseTimeout(cfg.EndorseTimeout),
		client.WithSubmitTimeout(cfg.SubmitTimeout),
		client.WithCommitStatusTimeout(cfg.CommitTimeout),
	)
	if err != nil {
		conn.Close()
		return nil, nil, err
	}

	return gw, conn, nil
}

func newIdentity(cfg FabricConfig) (*identity.X509Identity, error) {
	certPEM, err := os.ReadFile(cfg.CertPath)
	if err != nil {
		return nil, err
	}
	cert, err := identity.CertificateFromPEM(certPEM)
	if err != nil {
		return nil, err
	}
	return identity.NewX509Identity(cfg.MSPID, cert)
}

func newSigner(cfg FabricConfig) (identity.Sign, error) {
	keyPEM, err := os.ReadFile(cfg.KeyPath)
	if err != nil {
		return nil, err
	}

	block, _ := pem.Decode(keyPEM)
	if block == nil {
		return nil, fmt.Errorf("failed to decode private key PEM")
	}

	if pk, err := x509.ParsePKCS8PrivateKey(block.Bytes); err == nil {
		switch typed := pk.(type) {
		case *rsa.PrivateKey:
			return identity.NewPrivateKeySign(typed)
		case *ecdsa.PrivateKey:
			return identity.NewPrivateKeySign(typed)
		}
	}
	if pk, err := x509.ParsePKCS1PrivateKey(block.Bytes); err == nil {
		return identity.NewPrivateKeySign(pk)
	}
	if pk, err := x509.ParseECPrivateKey(block.Bytes); err == nil {
		return identity.NewPrivateKeySign(pk)
	}

	if pk, err := identity.PrivateKeyFromPEM(keyPEM); err == nil {
		return identity.NewPrivateKeySign(pk)
	}

	return nil, fmt.Errorf("unsupported private key format")
}

func certPoolFromPEM(cert []byte) *x509.CertPool {
	pool := x509.NewCertPool()
	pool.AppendCertsFromPEM(cert)
	return pool
}
