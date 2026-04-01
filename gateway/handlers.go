package main

import (
	"encoding/json"
	"errors"
	"log"
	"net/http"

	"github.com/hyperledger/fabric-gateway/pkg/client"
)

func (s *Server) routes() {
	s.mux.HandleFunc("POST /api/labels", s.deviceAuth(s.handleCreateLabel))
	s.mux.HandleFunc("GET /api/labels/counter", s.deviceAuth(s.handleGetLabelCounter))
	s.mux.HandleFunc("GET /api/labels/{id}", s.deviceAuth(s.handleGetLabel))
	s.mux.HandleFunc("POST /api/labels/{id}/mark-sent", s.deviceAuth(s.handleMarkAsSent))
	s.mux.HandleFunc("POST /api/labels/{id}/mark-received", s.deviceAuth(s.handleMarkAsReceived))
	s.mux.HandleFunc("GET /api/devices/me", s.deviceAuth(s.handleDeviceMe))

	s.mux.HandleFunc("POST /api/admin/init", s.adminAuth(s.handleInitOwner))
	s.mux.HandleFunc("POST /api/admin/authorize-device", s.adminAuth(s.handleAuthorizeDevice))
	s.mux.HandleFunc("POST /api/admin/authorize-label-creator", s.adminAuth(s.handleAuthorizeLabelCreator))
}

type createLabelRequest struct {
	LabelID  string `json:"labelId"`
	Sender   string `json:"sender"`
	Receiver string `json:"receiver"`
	Data     string `json:"data"`
}

func (s *Server) handleCreateLabel(w http.ResponseWriter, r *http.Request) {
	var req createLabelRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}
	if req.LabelID == "" || req.Sender == "" || req.Receiver == "" {
		writeError(w, http.StatusBadRequest, "labelId, sender, receiver are required")
		return
	}
	gw := gatewayFromCtx(r.Context())
	_, err := s.contract(gw).SubmitTransaction("CreateLabel", req.LabelID, req.Sender, req.Receiver, req.Data)
	if err != nil {
		writeFabricError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, map[string]string{"labelId": req.LabelID, "status": "created"})
}

func (s *Server) handleMarkAsSent(w http.ResponseWriter, r *http.Request) {
	labelID := r.PathValue("id")
	gw := gatewayFromCtx(r.Context())
	_, err := s.contract(gw).SubmitTransaction("MarkAsSent", labelID)
	if err != nil {
		writeFabricError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"labelId": labelID, "status": "sent"})
}

func (s *Server) handleMarkAsReceived(w http.ResponseWriter, r *http.Request) {
	labelID := r.PathValue("id")
	gw := gatewayFromCtx(r.Context())
	_, err := s.contract(gw).SubmitTransaction("MarkAsReceived", labelID)
	if err != nil {
		writeFabricError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"labelId": labelID, "status": "received"})
}

func (s *Server) handleGetLabel(w http.ResponseWriter, r *http.Request) {
	labelID := r.PathValue("id")
	gw := gatewayFromCtx(r.Context())
	result, err := s.contract(gw).EvaluateTransaction("GetLabel", labelID)
	if err != nil {
		writeFabricError(w, err)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(result)
}

func (s *Server) handleGetLabelCounter(w http.ResponseWriter, r *http.Request) {
	gw := gatewayFromCtx(r.Context())
	result, err := s.contract(gw).EvaluateTransaction("GetLabelCounter")
	if err != nil {
		writeFabricError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"counter": string(result)})
}

func (s *Server) handleDeviceMe(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"deviceId": deviceIDFromCtx(r.Context())})
}

func (s *Server) handleInitOwner(w http.ResponseWriter, r *http.Request) {
	_, err := s.contract(s.adminGateway).SubmitTransaction("InitOwner")
	if err != nil {
		writeFabricError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "owner initialized"})
}

type authorizeDeviceRequest struct {
	Account    string `json:"account"`
	UUID       string `json:"uuid"`
	AsSender   bool   `json:"asSender"`
	AsReceiver bool   `json:"asReceiver"`
	Status     bool   `json:"status"`
}

func (s *Server) handleAuthorizeDevice(w http.ResponseWriter, r *http.Request) {
	var req authorizeDeviceRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}
	if req.Account == "" {
		writeError(w, http.StatusBadRequest, "account is required")
		return
	}
	_, err := s.contract(s.adminGateway).SubmitTransaction(
		"SetIoTAuthorization",
		req.Account, req.UUID, boolStr(req.AsSender), boolStr(req.AsReceiver), boolStr(req.Status),
	)
	if err != nil {
		writeFabricError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok", "account": req.Account})
}

type authorizeLabelCreatorRequest struct {
	Account string `json:"account"`
	Status  bool   `json:"status"`
}

func (s *Server) handleAuthorizeLabelCreator(w http.ResponseWriter, r *http.Request) {
	var req authorizeLabelCreatorRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}
	if req.Account == "" {
		writeError(w, http.StatusBadRequest, "account is required")
		return
	}
	_, err := s.contract(s.adminGateway).SubmitTransaction(
		"SetLabelCreatorAuthorization",
		req.Account, boolStr(req.Status),
	)
	if err != nil {
		writeFabricError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok", "account": req.Account})
}

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Printf("writeJSON encode error: %v", err)
	}
}

func writeError(w http.ResponseWriter, code int, msg string) {
	writeJSON(w, code, map[string]string{"error": msg})
}

func writeFabricError(w http.ResponseWriter, err error) {
	log.Printf("Fabric error: %v", err)
	var endorseErr *client.EndorseError
	var submitErr *client.SubmitError
	var commitErr *client.CommitError
	switch {
	case errors.As(err, &endorseErr):
		writeError(w, http.StatusBadRequest, endorseErr.Error())
	case errors.As(err, &submitErr):
		writeError(w, http.StatusBadRequest, submitErr.Error())
	case errors.As(err, &commitErr):
		writeError(w, http.StatusBadRequest, commitErr.Error())
	default:
		writeError(w, http.StatusInternalServerError, err.Error())
	}
}

func boolStr(b bool) string {
	if b {
		return "true"
	}
	return "false"
}
