FROM golang:1.22.5-alpine
ADD . /go/src/hallo-world
RUN go install hallo-world

FROM alpine:3.18
COPY --from=0 /go/bin/hallo-world /hallo-world.
EXPOSE 8080
CMD ["./hallo-world"]