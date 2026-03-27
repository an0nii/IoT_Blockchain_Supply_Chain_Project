package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"

	"github.com/go-chi/chi/v5"
	"github.com/hyperledger/fabric-gateway/pkg/client"
	"google.golang.org/grpc"
)

type handler struct {
	cfg FabricConfig
}

func newHandler(cfg FabricConfig) *handler {
	return &handler{cfg: cfg}
}

type authorizeIotRequest struct {
	Account    string `json:"account"`
	AsSender   bool   `json:"asSender"`
	AsReceiver bool   `json:"asReceiver"`
	Status     bool   `json:"status"`
}

type createLabelRequest struct {
	LabelID  string `json:"labelId"`
	Sender   string `json:"sender"`
	Receiver string `json:"receiver"`
	Data     string `json:"data"`
}

func (h *handler) authorizeIot(w http.ResponseWriter, r *http.Request) {
	var payload authorizeIotRequest
	if err := decodeJSON(r, &payload); err != nil {
		writeError(w, http.StatusBadRequest, err)
		return
	}

	gateway, conn, contract, err := h.getContract()
	if err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}
	defer conn.Close()
	defer gateway.Close()

	_, err = contract.SubmitTransaction(
		"SetIoTAuthorization",
		payload.Account,
		fmt.Sprintf("%t", payload.AsSender),
		fmt.Sprintf("%t", payload.AsReceiver),
		fmt.Sprintf("%t", payload.Status),
	)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}

	writeJSON(w, http.StatusOK, map[string]any{"ok": true})
}

func (h *handler) createLabel(w http.ResponseWriter, r *http.Request) {
	var payload createLabelRequest
	if err := decodeJSON(r, &payload); err != nil {
		writeError(w, http.StatusBadRequest, err)
		return
	}

	gateway, conn, contract, err := h.getContract()
	if err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}
	defer conn.Close()
	defer gateway.Close()

	_, err = contract.SubmitTransaction("CreateLabel", payload.LabelID, payload.Sender, payload.Receiver, payload.Data)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}

	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "labelId": payload.LabelID})
}

func (h *handler) markSent(w http.ResponseWriter, r *http.Request) {
	labelID := chi.URLParam(r, "labelId")

	gateway, conn, contract, err := h.getContract()
	if err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}
	defer conn.Close()
	defer gateway.Close()

	_, err = contract.SubmitTransaction("MarkAsSent", labelID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}

	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "labelId": labelID})
}

func (h *handler) markReceived(w http.ResponseWriter, r *http.Request) {
	labelID := chi.URLParam(r, "labelId")

	gateway, conn, contract, err := h.getContract()
	if err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}
	defer conn.Close()
	defer gateway.Close()

	_, err = contract.SubmitTransaction("MarkAsReceived", labelID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}

	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "labelId": labelID})
}

func (h *handler) getLabel(w http.ResponseWriter, r *http.Request) {
	labelID := chi.URLParam(r, "labelId")

	gateway, conn, contract, err := h.getContract()
	if err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}
	defer conn.Close()
	defer gateway.Close()

	result, err := contract.EvaluateTransaction("GetLabel", labelID)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}

	var payload any
	if err := json.Unmarshal(result, &payload); err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}

	writeJSON(w, http.StatusOK, map[string]any{"label": payload})
}

func (h *handler) getLabelCount(w http.ResponseWriter, r *http.Request) {
	gateway, conn, contract, err := h.getContract()
	if err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}
	defer conn.Close()
	defer gateway.Close()

	result, err := contract.EvaluateTransaction("GetLabelCounter")
	if err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}

	writeJSON(w, http.StatusOK, map[string]any{"count": string(result)})
}

func (h *handler) listLabels(w http.ResponseWriter, r *http.Request) {
	gateway, conn, contract, err := h.getContract()
	if err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}
	defer conn.Close()
	defer gateway.Close()

	countBytes, err := contract.EvaluateTransaction("GetLabelCounter")
	if err != nil {
		writeError(w, http.StatusInternalServerError, err)
		return
	}

	count := 0
	if parsed, err := strconv.Atoi(string(countBytes)); err == nil {
		count = parsed
	}

	labels := make([]any, 0)
	for idx := 1; idx <= count; idx++ {
		labelBytes, err := contract.EvaluateTransaction("GetLabel", fmt.Sprintf("%d", idx))
		if err != nil {
			continue
		}
		var label any
		if err := json.Unmarshal(labelBytes, &label); err != nil {
			continue
		}
		labels = append(labels, label)
	}

	writeJSON(w, http.StatusOK, map[string]any{"labels": labels, "count": count})
}

func (h *handler) getContract() (*client.Gateway, *grpc.ClientConn, *client.Contract, error) {
	gw, conn, err := newGateway(h.cfg)
	if err != nil {
		return nil, nil, nil, err
	}

	network := gw.GetNetwork(h.cfg.Channel)
	contract := network.GetContract(h.cfg.Chaincode)
	return gw, conn, contract, nil
}
