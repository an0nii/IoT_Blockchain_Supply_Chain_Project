package main

import (
	"encoding/json"
	"fmt"
	"strconv"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

const (
	ownerKey        = "owner"
	labelCounterKey = "labelCounter"
	labelPrefix     = "label"
	authPrefix      = "auth"

	roleLabelCreator = "labelCreator"
	roleIoTSender    = "iotSender"
	roleIoTReceiver  = "iotReceiver"
)

type IoTContract struct {
	contractapi.Contract
}

func (c *IoTContract) InitOwner(ctx contractapi.TransactionContextInterface) error {
	owner, err := c.getOwner(ctx)
	if err != nil {
		return err
	}
	if owner != "" {
		return fmt.Errorf("owner already initialized")
	}

	caller, err := c.getClientID(ctx)
	if err != nil {
		return err
	}
	if err := ctx.GetStub().PutState(ownerKey, []byte(caller)); err != nil {
		return err
	}
	return c.setAuthorization(ctx, roleLabelCreator, caller, true)
}

func (c *IoTContract) SetLabelCreatorAuthorization(ctx contractapi.TransactionContextInterface, account string, status bool) error {
	if err := c.requireOwner(ctx); err != nil {
		return err
	}
	return c.setAuthorization(ctx, roleLabelCreator, account, status)
}

func (c *IoTContract) SetIoTAuthorization(ctx contractapi.TransactionContextInterface, account string, asSender bool, asReceiver bool, status bool) error {
	if err := c.requireOwner(ctx); err != nil {
		return err
	}
	if status && asSender && asReceiver {
		return fmt.Errorf("device cannot be both sender and receiver")
	}

	if asSender {
		if err := c.setAuthorization(ctx, roleIoTSender, account, status); err != nil {
			return err
		}
		if status {
			if err := c.setAuthorization(ctx, roleIoTReceiver, account, false); err != nil {
				return err
			}
		}
	}
	if asReceiver {
		if err := c.setAuthorization(ctx, roleIoTReceiver, account, status); err != nil {
			return err
		}
		if status {
			if err := c.setAuthorization(ctx, roleIoTSender, account, false); err != nil {
				return err
			}
		}
	}
	return nil
}

func (c *IoTContract) CreateLabel(ctx contractapi.TransactionContextInterface, labelID string, sender string, receiver string, data string) error {
	if err := c.requireAuthorized(ctx, roleLabelCreator); err != nil {
		return err
	}
	if receiver == "" {
		return fmt.Errorf("invalid receiver")
	}
	if sender == "" {
		return fmt.Errorf("invalid sender")
	}
	if ok, err := c.isAuthorized(ctx, roleIoTSender, sender); err != nil {
		return err
	} else if !ok {
		return fmt.Errorf("sender not authorized")
	}
	if ok, err := c.isAuthorized(ctx, roleIoTReceiver, receiver); err != nil {
		return err
	} else if !ok {
		return fmt.Errorf("receiver not authorized")
	}

	labelKey, err := ctx.GetStub().CreateCompositeKey(labelPrefix, []string{labelID})
	if err != nil {
		return err
	}
	if existing, err := ctx.GetStub().GetState(labelKey); err != nil {
		return err
	} else if existing != nil {
		return fmt.Errorf("label already exists")
	}

	counter, err := c.incrementLabelCounter(ctx)
	if err != nil {
		return err
	}

	label := Label{
		ID:       labelID,
		Sender:   sender,
		Receiver: receiver,
		Data:     data,
		Sent:     false,
		Received: false,
	}
	payload, err := json.Marshal(label)
	if err != nil {
		return err
	}
	if err := ctx.GetStub().PutState(labelKey, payload); err != nil {
		return err
	}

	event := LabelCreatedEvent{
		LabelID:  labelID,
		Counter:  counter,
		Sender:   sender,
		Receiver: receiver,
	}
	return c.emitEvent(ctx, "LabelCreated", event)
}

func (c *IoTContract) MarkAsSent(ctx contractapi.TransactionContextInterface, labelID string) error {
	if err := c.requireAuthorized(ctx, roleIoTSender); err != nil {
		return err
	}

	caller, err := c.getClientID(ctx)
	if err != nil {
		return err
	}

	label, labelKey, err := c.getLabel(ctx, labelID)
	if err != nil {
		return err
	}
	if label.Sent {
		return fmt.Errorf("label already marked as sent")
	}
	if label.Sender != caller {
		return fmt.Errorf("not the sender of this label")
	}

	label.Sent = true
	payload, err := json.Marshal(label)
	if err != nil {
		return err
	}
	if err := ctx.GetStub().PutState(labelKey, payload); err != nil {
		return err
	}

	event := LabelSentEvent{LabelID: labelID, Sender: caller}
	return c.emitEvent(ctx, "LabelSent", event)
}

func (c *IoTContract) MarkAsReceived(ctx contractapi.TransactionContextInterface, labelID string) error {
	if err := c.requireAuthorized(ctx, roleIoTReceiver); err != nil {
		return err
	}

	caller, err := c.getClientID(ctx)
	if err != nil {
		return err
	}

	label, labelKey, err := c.getLabel(ctx, labelID)
	if err != nil {
		return err
	}
	if !label.Sent {
		return fmt.Errorf("label not marked as sent")
	}
	if label.Received {
		return fmt.Errorf("label already marked as received")
	}
	if label.Receiver != caller {
		return fmt.Errorf("not the receiver of this label")
	}

	label.Received = true
	payload, err := json.Marshal(label)
	if err != nil {
		return err
	}
	if err := ctx.GetStub().PutState(labelKey, payload); err != nil {
		return err
	}

	event := LabelReceivedEvent{LabelID: labelID, Receiver: caller}
	return c.emitEvent(ctx, "LabelReceived", event)
}

func (c *IoTContract) GetLabel(ctx contractapi.TransactionContextInterface, labelID string) (*Label, error) {
	label, _, err := c.getLabel(ctx, labelID)
	if err != nil {
		return nil, err
	}
	return &label, nil
}

func (c *IoTContract) GetLabelCounter(ctx contractapi.TransactionContextInterface) (uint64, error) {
	return c.getLabelCounter(ctx)
}

func (c *IoTContract) getLabel(ctx contractapi.TransactionContextInterface, labelID string) (Label, string, error) {
	if labelID == "" {
		return Label{}, "", fmt.Errorf("label id is required")
	}

	labelKey, err := ctx.GetStub().CreateCompositeKey(labelPrefix, []string{labelID})
	if err != nil {
		return Label{}, "", err
	}
	payload, err := ctx.GetStub().GetState(labelKey)
	if err != nil {
		return Label{}, "", err
	}
	if payload == nil {
		return Label{}, "", fmt.Errorf("label does not exist")
	}

	var label Label
	if err := json.Unmarshal(payload, &label); err != nil {
		return Label{}, "", err
	}
	return label, labelKey, nil
}

func (c *IoTContract) incrementLabelCounter(ctx contractapi.TransactionContextInterface) (uint64, error) {
	counter, err := c.getLabelCounter(ctx)
	if err != nil {
		return 0, err
	}
	counter++
	if err := c.setLabelCounter(ctx, counter); err != nil {
		return 0, err
	}
	return counter, nil
}

func (c *IoTContract) getLabelCounter(ctx contractapi.TransactionContextInterface) (uint64, error) {
	payload, err := ctx.GetStub().GetState(labelCounterKey)
	if err != nil {
		return 0, err
	}
	if payload == nil {
		return 0, nil
	}
	counter, err := strconv.ParseUint(string(payload), 10, 64)
	if err != nil {
		return 0, err
	}
	return counter, nil
}

func (c *IoTContract) setLabelCounter(ctx contractapi.TransactionContextInterface, counter uint64) error {
	return ctx.GetStub().PutState(labelCounterKey, []byte(strconv.FormatUint(counter, 10)))
}

func (c *IoTContract) emitEvent(ctx contractapi.TransactionContextInterface, name string, payload any) error {
	bytes, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	return ctx.GetStub().SetEvent(name, bytes)
}

func (c *IoTContract) requireOwner(ctx contractapi.TransactionContextInterface) error {
	owner, err := c.getOwner(ctx)
	if err != nil {
		return err
	}
	if owner == "" {
		return fmt.Errorf("owner not initialized")
	}

	caller, err := c.getClientID(ctx)
	if err != nil {
		return err
	}
	if owner != caller {
		return fmt.Errorf("not an owner")
	}
	return nil
}

func (c *IoTContract) getOwner(ctx contractapi.TransactionContextInterface) (string, error) {
	payload, err := ctx.GetStub().GetState(ownerKey)
	if err != nil {
		return "", err
	}
	if payload == nil {
		return "", nil
	}
	return string(payload), nil
}

func (c *IoTContract) getClientID(ctx contractapi.TransactionContextInterface) (string, error) {
	identity, err := ctx.GetClientIdentity().GetID()
	if err != nil {
		return "", err
	}
	return identity, nil
}

func (c *IoTContract) requireAuthorized(ctx contractapi.TransactionContextInterface, role string) error {
	caller, err := c.getClientID(ctx)
	if err != nil {
		return err
	}

	ok, err := c.isAuthorized(ctx, role, caller)
	if err != nil {
		return err
	}
	if !ok {
		return fmt.Errorf("not authorized: %s", role)
	}
	return nil
}

func (c *IoTContract) requireAuthorizedAny(ctx contractapi.TransactionContextInterface, roles ...string) error {
	caller, err := c.getClientID(ctx)
	if err != nil {
		return err
	}

	for _, role := range roles {
		ok, err := c.isAuthorized(ctx, role, caller)
		if err != nil {
			return err
		}
		if ok {
			return nil
		}
	}

	return fmt.Errorf("not authorized")
}

func (c *IoTContract) isAuthorized(ctx contractapi.TransactionContextInterface, role string, account string) (bool, error) {
	if account == "" {
		return false, fmt.Errorf("account is required")
	}
	key, err := ctx.GetStub().CreateCompositeKey(authPrefix, []string{role, account})
	if err != nil {
		return false, err
	}
	payload, err := ctx.GetStub().GetState(key)
	if err != nil {
		return false, err
	}
	return payload != nil, nil
}

func (c *IoTContract) setAuthorization(ctx contractapi.TransactionContextInterface, role string, account string, status bool) error {
	if account == "" {
		return fmt.Errorf("account is required")
	}
	key, err := ctx.GetStub().CreateCompositeKey(authPrefix, []string{role, account})
	if err != nil {
		return err
	}
	if status {
		return ctx.GetStub().PutState(key, []byte{1})
	}
	return ctx.GetStub().DelState(key)
}
