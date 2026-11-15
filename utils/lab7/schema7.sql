--
-- PostgreSQL database dump
--

\restrict 5Ohr13FbsHAaHjs1cMOVzdzTfe8seDRVRybf0deIMsRuf9cY8km78ZLvrCrDRQR

-- Dumped from database version 14.23 (Ubuntu 14.23-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.23 (Ubuntu 14.23-0ubuntu0.22.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: class_configuration_parameter; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.class_configuration_parameter (
    id integer NOT NULL,
    class_id integer NOT NULL,
    parameter_id integer NOT NULL,
    flag_conf boolean NOT NULL,
    required boolean NOT NULL,
    display_order integer NOT NULL,
    min_value numeric(18,6),
    max_value numeric(18,6),
    CONSTRAINT ck_configuration_range CHECK (((min_value IS NULL) OR (max_value IS NULL) OR (min_value <= max_value)))
);


--
-- Name: class_configuration_parameter_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.class_configuration_parameter_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: class_configuration_parameter_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.class_configuration_parameter_id_seq OWNED BY public.class_configuration_parameter.id;


--
-- Name: configuration_constraint; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.configuration_constraint (
    id integer NOT NULL,
    template_id integer NOT NULL,
    name character varying(255) NOT NULL,
    expression jsonb NOT NULL
);


--
-- Name: configuration_constraint_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.configuration_constraint_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: configuration_constraint_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.configuration_constraint_id_seq OWNED BY public.configuration_constraint.id;


--
-- Name: configuration_function; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.configuration_function (
    id integer NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(255) NOT NULL,
    definition jsonb NOT NULL
);


--
-- Name: configuration_function_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.configuration_function_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: configuration_function_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.configuration_function_id_seq OWNED BY public.configuration_function.id;


--
-- Name: customer_order; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_order (
    id integer NOT NULL,
    number character varying(50) NOT NULL,
    customer character varying(255) NOT NULL,
    order_date date NOT NULL,
    status character varying(20) NOT NULL,
    ho_id integer,
    CONSTRAINT ck_customer_order_status CHECK (((status)::text = ANY ((ARRAY['draft'::character varying, 'agreed'::character varying])::text[])))
);


--
-- Name: customer_order_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.customer_order_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: customer_order_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.customer_order_id_seq OWNED BY public.customer_order.id;


--
-- Name: customer_order_position; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_order_position (
    id integer NOT NULL,
    order_id integer NOT NULL,
    number integer NOT NULL,
    item_id integer NOT NULL,
    quantity numeric(18,6) NOT NULL,
    CONSTRAINT ck_order_position_quantity CHECK (((quantity > (0)::numeric) AND (number > 0)))
);


--
-- Name: customer_order_position_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.customer_order_position_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: customer_order_position_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.customer_order_position_id_seq OWNED BY public.customer_order_position.id;


--
-- Name: item_configuration; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.item_configuration (
    item_id integer NOT NULL,
    kind character varying(20) NOT NULL,
    template_id integer,
    CONSTRAINT ck_item_configuration_kind CHECK (((((kind)::text = 'template'::text) AND (template_id IS NULL)) OR (((kind)::text = 'variant'::text) AND (template_id IS NOT NULL) AND (template_id <> item_id))))
);


--
-- Name: variant_parameter_value; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.variant_parameter_value (
    item_id integer NOT NULL,
    parameter_id integer NOT NULL,
    value jsonb NOT NULL
);


--
-- Name: class_configuration_parameter id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.class_configuration_parameter ALTER COLUMN id SET DEFAULT nextval('public.class_configuration_parameter_id_seq'::regclass);


--
-- Name: configuration_constraint id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configuration_constraint ALTER COLUMN id SET DEFAULT nextval('public.configuration_constraint_id_seq'::regclass);


--
-- Name: configuration_function id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configuration_function ALTER COLUMN id SET DEFAULT nextval('public.configuration_function_id_seq'::regclass);


--
-- Name: customer_order id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_order ALTER COLUMN id SET DEFAULT nextval('public.customer_order_id_seq'::regclass);


--
-- Name: customer_order_position id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_order_position ALTER COLUMN id SET DEFAULT nextval('public.customer_order_position_id_seq'::regclass);


--
-- Name: class_configuration_parameter class_configuration_parameter_class_id_parameter_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.class_configuration_parameter
    ADD CONSTRAINT class_configuration_parameter_class_id_parameter_id_key UNIQUE (class_id, parameter_id);


--
-- Name: class_configuration_parameter class_configuration_parameter_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.class_configuration_parameter
    ADD CONSTRAINT class_configuration_parameter_pkey PRIMARY KEY (id);


--
-- Name: configuration_constraint configuration_constraint_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configuration_constraint
    ADD CONSTRAINT configuration_constraint_pkey PRIMARY KEY (id);


--
-- Name: configuration_constraint configuration_constraint_template_id_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configuration_constraint
    ADD CONSTRAINT configuration_constraint_template_id_name_key UNIQUE (template_id, name);


--
-- Name: configuration_function configuration_function_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configuration_function
    ADD CONSTRAINT configuration_function_code_key UNIQUE (code);


--
-- Name: configuration_function configuration_function_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configuration_function
    ADD CONSTRAINT configuration_function_pkey PRIMARY KEY (id);


--
-- Name: customer_order customer_order_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_order
    ADD CONSTRAINT customer_order_number_key UNIQUE (number);


--
-- Name: customer_order customer_order_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_order
    ADD CONSTRAINT customer_order_pkey PRIMARY KEY (id);


--
-- Name: customer_order_position customer_order_position_order_id_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_order_position
    ADD CONSTRAINT customer_order_position_order_id_number_key UNIQUE (order_id, number);


--
-- Name: customer_order_position customer_order_position_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_order_position
    ADD CONSTRAINT customer_order_position_pkey PRIMARY KEY (id);


--
-- Name: item_configuration item_configuration_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_configuration
    ADD CONSTRAINT item_configuration_pkey PRIMARY KEY (item_id);


--
-- Name: variant_parameter_value variant_parameter_value_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.variant_parameter_value
    ADD CONSTRAINT variant_parameter_value_pkey PRIMARY KEY (item_id, parameter_id);


--
-- Name: class_configuration_parameter class_configuration_parameter_class_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.class_configuration_parameter
    ADD CONSTRAINT class_configuration_parameter_class_id_fkey FOREIGN KEY (class_id) REFERENCES public.item_classifier(id);


--
-- Name: class_configuration_parameter class_configuration_parameter_parameter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.class_configuration_parameter
    ADD CONSTRAINT class_configuration_parameter_parameter_id_fkey FOREIGN KEY (parameter_id) REFERENCES public.parameter(id);


--
-- Name: configuration_constraint configuration_constraint_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.configuration_constraint
    ADD CONSTRAINT configuration_constraint_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.item(id);


--
-- Name: customer_order customer_order_ho_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_order
    ADD CONSTRAINT customer_order_ho_id_fkey FOREIGN KEY (ho_id) REFERENCES public.ho(id);


--
-- Name: customer_order_position customer_order_position_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_order_position
    ADD CONSTRAINT customer_order_position_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.item(id);


--
-- Name: customer_order_position customer_order_position_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_order_position
    ADD CONSTRAINT customer_order_position_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.customer_order(id);


--
-- Name: item_configuration item_configuration_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_configuration
    ADD CONSTRAINT item_configuration_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.item(id);


--
-- Name: item_configuration item_configuration_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_configuration
    ADD CONSTRAINT item_configuration_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.item(id);


--
-- Name: variant_parameter_value variant_parameter_value_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.variant_parameter_value
    ADD CONSTRAINT variant_parameter_value_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.item(id);


--
-- Name: variant_parameter_value variant_parameter_value_parameter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.variant_parameter_value
    ADD CONSTRAINT variant_parameter_value_parameter_id_fkey FOREIGN KEY (parameter_id) REFERENCES public.parameter(id);


--
-- PostgreSQL database dump complete
--

\unrestrict 5Ohr13FbsHAaHjs1cMOVzdzTfe8seDRVRybf0deIMsRuf9cY8km78ZLvrCrDRQR

