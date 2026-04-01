FROM golang:1.23-alpine AS builder

WORKDIR /app

COPY . .
RUN go mod tidy && go build -o gateway .

FROM alpine:3.21

RUN apk add --no-cache ca-certificates

WORKDIR /app

COPY --from=builder /app/gateway .

EXPOSE 3000

CMD ["./gateway"]
