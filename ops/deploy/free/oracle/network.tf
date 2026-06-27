# Minimal public networking: one VCN + public subnet + internet gateway, with a
# security list opening SSH (22) and HTTP/HTTPS (80/443) for Let's Encrypt + the app.

resource "oci_core_vcn" "mynd" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = ["10.0.0.0/16"]
  display_name   = "mynd-vcn"
  dns_label      = "mynd"
}

resource "oci_core_internet_gateway" "mynd" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.mynd.id
  display_name   = "mynd-igw"
}

resource "oci_core_route_table" "mynd" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.mynd.id
  display_name   = "mynd-rt"
  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.mynd.id
  }
}

resource "oci_core_security_list" "mynd" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.mynd.id
  display_name   = "mynd-sl"

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  # SSH
  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 22
      max = 22
    }
  }
  # HTTP (Let's Encrypt challenge + redirect)
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 80
      max = 80
    }
  }
  # HTTPS
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 443
      max = 443
    }
  }
}

resource "oci_core_subnet" "mynd" {
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.mynd.id
  cidr_block        = "10.0.1.0/24"
  display_name      = "mynd-public-subnet"
  route_table_id    = oci_core_route_table.mynd.id
  security_list_ids = [oci_core_security_list.mynd.id]
  dns_label         = "public"
  # Public subnet: instances get a public IP.
  prohibit_public_ip_on_vnic = false
}
