package main

import (
	"encoding/json"
	"log"
	"net/http"
	"time"

	"ticketly/booking-engine/internal/booking"
)

func main() {
	locker := booking.NewMemoryLocker(3 * time.Minute)
	engine := booking.NewEngine(locker)

	http.HandleFunc("/healthz", func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	})

	http.HandleFunc("/v1/reservations", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		var req booking.ReservationRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		res, err := engine.Reserve(r.Context(), req)
		if err != nil {
			http.Error(w, err.Error(), http.StatusConflict)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(res)
	})

	log.Println("booking engine listening on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

