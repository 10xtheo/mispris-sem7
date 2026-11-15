--
-- PostgreSQL database dump
--

\restrict gtaafkupBXChZCChDuoG5jgGP7lfylujPgzVZlnWibhDyYAqVYjZCXtRZMYVrw3

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
    name character varying(255) NOT NULL
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
    name character varying(255) NOT NULL
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
-- Name: rule_actual_argument; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rule_actual_argument (
    expression_id integer NOT NULL,
    number integer NOT NULL,
    name character varying(100),
    value_expression_id integer NOT NULL,
    CONSTRAINT ck_rule_actual_number CHECK ((number > 0))
);


--
-- Name: rule_constant; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rule_constant (
    id integer NOT NULL,
    value_type character varying(20) NOT NULL,
    value_text character varying NOT NULL,
    CONSTRAINT ck_rule_constant_type CHECK (((value_type)::text = ANY ((ARRAY['number'::character varying, 'string'::character varying, 'bool'::character varying])::text[])))
);


--
-- Name: rule_constant_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rule_constant_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rule_constant_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rule_constant_id_seq OWNED BY public.rule_constant.id;


--
-- Name: rule_constraint_root; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rule_constraint_root (
    constraint_id integer NOT NULL,
    expression_id integer NOT NULL
);


--
-- Name: rule_expression; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rule_expression (
    id integer NOT NULL,
    kind character varying(20) NOT NULL,
    function_id integer,
    operator_id integer,
    constant_id integer,
    parameter_name character varying(100),
    CONSTRAINT ck_rule_expression_kind CHECK (((((kind)::text = 'call'::text) AND (function_id IS NOT NULL) AND (operator_id IS NULL) AND (constant_id IS NULL) AND (parameter_name IS NULL)) OR (((kind)::text = 'op'::text) AND (function_id IS NULL) AND (operator_id IS NOT NULL) AND (constant_id IS NULL) AND (parameter_name IS NULL)) OR (((kind)::text = 'const'::text) AND (function_id IS NULL) AND (operator_id IS NULL) AND (constant_id IS NOT NULL) AND (parameter_name IS NULL)) OR (((kind)::text = 'param'::text) AND (function_id IS NULL) AND (operator_id IS NULL) AND (constant_id IS NULL) AND (parameter_name IS NOT NULL))))
);


--
-- Name: rule_expression_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rule_expression_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rule_expression_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rule_expression_id_seq OWNED BY public.rule_expression.id;


--
-- Name: rule_formal_argument; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rule_formal_argument (
    function_id integer NOT NULL,
    number integer NOT NULL,
    name character varying(100) NOT NULL,
    value_type character varying(20) NOT NULL,
    CONSTRAINT ck_rule_formal_number CHECK ((number > 0))
);


--
-- Name: rule_function_class; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rule_function_class (
    id integer NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(255) NOT NULL,
    parent_id integer
);


--
-- Name: rule_function_class_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rule_function_class_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rule_function_class_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rule_function_class_id_seq OWNED BY public.rule_function_class.id;


--
-- Name: rule_function_definition; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rule_function_definition (
    function_id integer NOT NULL,
    class_id integer NOT NULL,
    result_type character varying(20) NOT NULL,
    body_id integer NOT NULL
);


--
-- Name: rule_operator; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rule_operator (
    id integer NOT NULL,
    code character varying(20) NOT NULL,
    class_id integer NOT NULL,
    result_type character varying(20) NOT NULL
);


--
-- Name: rule_operator_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rule_operator_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rule_operator_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rule_operator_id_seq OWNED BY public.rule_operator.id;


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
-- Name: rule_constant id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_constant ALTER COLUMN id SET DEFAULT nextval('public.rule_constant_id_seq'::regclass);


--
-- Name: rule_expression id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_expression ALTER COLUMN id SET DEFAULT nextval('public.rule_expression_id_seq'::regclass);


--
-- Name: rule_function_class id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_function_class ALTER COLUMN id SET DEFAULT nextval('public.rule_function_class_id_seq'::regclass);


--
-- Name: rule_operator id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_operator ALTER COLUMN id SET DEFAULT nextval('public.rule_operator_id_seq'::regclass);


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
-- Name: rule_actual_argument rule_actual_argument_expression_id_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_actual_argument
    ADD CONSTRAINT rule_actual_argument_expression_id_name_key UNIQUE (expression_id, name);


--
-- Name: rule_actual_argument rule_actual_argument_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_actual_argument
    ADD CONSTRAINT rule_actual_argument_pkey PRIMARY KEY (expression_id, number);


--
-- Name: rule_constant rule_constant_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_constant
    ADD CONSTRAINT rule_constant_pkey PRIMARY KEY (id);


--
-- Name: rule_constraint_root rule_constraint_root_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_constraint_root
    ADD CONSTRAINT rule_constraint_root_pkey PRIMARY KEY (constraint_id);


--
-- Name: rule_expression rule_expression_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_expression
    ADD CONSTRAINT rule_expression_pkey PRIMARY KEY (id);


--
-- Name: rule_formal_argument rule_formal_argument_function_id_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_formal_argument
    ADD CONSTRAINT rule_formal_argument_function_id_name_key UNIQUE (function_id, name);


--
-- Name: rule_formal_argument rule_formal_argument_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_formal_argument
    ADD CONSTRAINT rule_formal_argument_pkey PRIMARY KEY (function_id, number);


--
-- Name: rule_function_class rule_function_class_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_function_class
    ADD CONSTRAINT rule_function_class_code_key UNIQUE (code);


--
-- Name: rule_function_class rule_function_class_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_function_class
    ADD CONSTRAINT rule_function_class_pkey PRIMARY KEY (id);


--
-- Name: rule_function_definition rule_function_definition_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_function_definition
    ADD CONSTRAINT rule_function_definition_pkey PRIMARY KEY (function_id);


--
-- Name: rule_operator rule_operator_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_operator
    ADD CONSTRAINT rule_operator_code_key UNIQUE (code);


--
-- Name: rule_operator rule_operator_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_operator
    ADD CONSTRAINT rule_operator_pkey PRIMARY KEY (id);


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
-- Name: rule_actual_argument rule_actual_argument_expression_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_actual_argument
    ADD CONSTRAINT rule_actual_argument_expression_id_fkey FOREIGN KEY (expression_id) REFERENCES public.rule_expression(id);


--
-- Name: rule_actual_argument rule_actual_argument_value_expression_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_actual_argument
    ADD CONSTRAINT rule_actual_argument_value_expression_id_fkey FOREIGN KEY (value_expression_id) REFERENCES public.rule_expression(id);


--
-- Name: rule_constraint_root rule_constraint_root_constraint_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_constraint_root
    ADD CONSTRAINT rule_constraint_root_constraint_id_fkey FOREIGN KEY (constraint_id) REFERENCES public.configuration_constraint(id);


--
-- Name: rule_constraint_root rule_constraint_root_expression_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_constraint_root
    ADD CONSTRAINT rule_constraint_root_expression_id_fkey FOREIGN KEY (expression_id) REFERENCES public.rule_expression(id);


--
-- Name: rule_expression rule_expression_constant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_expression
    ADD CONSTRAINT rule_expression_constant_id_fkey FOREIGN KEY (constant_id) REFERENCES public.rule_constant(id);


--
-- Name: rule_expression rule_expression_function_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_expression
    ADD CONSTRAINT rule_expression_function_id_fkey FOREIGN KEY (function_id) REFERENCES public.configuration_function(id);


--
-- Name: rule_expression rule_expression_operator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_expression
    ADD CONSTRAINT rule_expression_operator_id_fkey FOREIGN KEY (operator_id) REFERENCES public.rule_operator(id);


--
-- Name: rule_formal_argument rule_formal_argument_function_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_formal_argument
    ADD CONSTRAINT rule_formal_argument_function_id_fkey FOREIGN KEY (function_id) REFERENCES public.configuration_function(id);


--
-- Name: rule_function_class rule_function_class_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_function_class
    ADD CONSTRAINT rule_function_class_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.rule_function_class(id);


--
-- Name: rule_function_definition rule_function_definition_body_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_function_definition
    ADD CONSTRAINT rule_function_definition_body_id_fkey FOREIGN KEY (body_id) REFERENCES public.rule_expression(id);


--
-- Name: rule_function_definition rule_function_definition_class_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_function_definition
    ADD CONSTRAINT rule_function_definition_class_id_fkey FOREIGN KEY (class_id) REFERENCES public.rule_function_class(id);


--
-- Name: rule_function_definition rule_function_definition_function_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_function_definition
    ADD CONSTRAINT rule_function_definition_function_id_fkey FOREIGN KEY (function_id) REFERENCES public.configuration_function(id);


--
-- Name: rule_operator rule_operator_class_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rule_operator
    ADD CONSTRAINT rule_operator_class_id_fkey FOREIGN KEY (class_id) REFERENCES public.rule_function_class(id);


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

\unrestrict gtaafkupBXChZCChDuoG5jgGP7lfylujPgzVZlnWibhDyYAqVYjZCXtRZMYVrw3

