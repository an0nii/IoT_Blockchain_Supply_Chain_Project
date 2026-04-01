package main

import (
	"context"
	"net/http"

	"github.com/hyperledger/fabric-gateway/pkg/client"
)

type contextKey string

const (
	ctxGateway  contextKey = "gateway"
	ctxDeviceID contextKey = "deviceId"
)

func (s *Server) deviceAuth(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		apiKey := r.Header.Get("X-Device-Key")
		if apiKey == "" {
			writeError(w, http.StatusUnauthorized, "missing X-Device-Key header")
			return
		}
		entry, ok := s.devices[apiKey]
		if !ok {
			writeError(w, http.StatusUnauthorized, "unknown device key")
			return
		}
		ctx := context.WithValue(r.Context(), ctxGateway, entry.gateway)
		ctx = context.WithValue(ctx, ctxDeviceID, entry.deviceID)
		next(w, r.WithContext(ctx))
	}
}

func (s *Server) adminAuth(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-Admin-Key") != s.cfg.AdminAPIKey {
			writeError(w, http.StatusUnauthorized, "invalid admin key")
			return
		}
		next(w, r)
	}
}

func gatewayFromCtx(ctx context.Context) *client.Gateway {
	return ctx.Value(ctxGateway).(*client.Gateway)
}

func deviceIDFromCtx(ctx context.Context) string {
	return ctx.Value(ctxDeviceID).(string)
}
