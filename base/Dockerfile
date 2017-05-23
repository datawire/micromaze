FROM ubuntu:14.04

MAINTAINER Datawire <flynn@datawire.io>
LABEL PROJECT_REPO_URL         = "git@github.com:datawire/snc-ident.git" \
      PROJECT_REPO_BROWSER_URL = "https://github.com/datawire/snc-ident \
      DESCRIPTION              = "Service Base Image" \
      VENDOR                   = "Datawire" \
      VENDOR_URL               = "https://datawire.io/"

# This Dockerfile is set up to install all the application-specific stuff into
# /application.
#
# NOTE: If you don't know what you're doing, it's probably a mistake to 
# blindly hack up this file.

# We need curl, pip, and dnsutils (for nslookup).
RUN apt-get update && apt-get -q install -y \
    curl \
    python-pip \
    dnsutils
