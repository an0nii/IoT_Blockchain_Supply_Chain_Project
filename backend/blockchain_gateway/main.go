package main

import (
	"log"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

func main() {
	cfg, err := loadConfig()
	if err != nil {
		log.Fatalf("config error: %v", err)
	}

	r := chi.NewRouter()
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Logger)
	r.Use(corsMiddleware)

	h := newHandler(cfg)
	r.Route("/api", func(r chi.Router) {
		r.Route("/blockchain", func(r chi.Router) {
			r.Post("/authorize-iot", h.authorizeIot)
			r.Post("/labels", h.createLabel)
			r.Get("/labels", h.listLabels)
			r.Get("/labels/count", h.getLabelCount)
			r.Post("/labels/{labelId}/sent", h.markSent)
			r.Post("/labels/{labelId}/received", h.markReceived)
			r.Get("/labels/{labelId}", h.getLabel)
		})
	})

	addr := ":" + cfg.HTTPPort
	log.Printf("blockchain API listening on %s", addr)
	if err := http.ListenAndServe(addr, r); err != nil {
		log.Fatalf("server error: %v", err)
	}
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}
