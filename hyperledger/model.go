package main

type Label struct {
	ID       string `json:"id"`
	Sender   string `json:"sender"`
	Receiver string `json:"receiver"`
	Data     string `json:"data,omitempty"`
	Sent     bool   `json:"sent"`
	Received bool   `json:"received"`
}

type LabelCreatedEvent struct {
	LabelID  string `json:"labelId"`
	Counter  uint64 `json:"counter"`
	Sender   string `json:"sender"`
	Receiver string `json:"receiver"`
}

type LabelSentEvent struct {
	LabelID string `json:"labelId"`
	Sender  string `json:"sender"`
}

type LabelReceivedEvent struct {
	LabelID  string `json:"labelId"`
	Receiver string `json:"receiver"`
}
