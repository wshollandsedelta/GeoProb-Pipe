import geoprob_pipe.calculations.physical_components.piping as pc_piping


def limit_state_wshd(
    # Geometry parameters
    # TODO: Moet L_but L_buk worden? Of L_spreidingslengte?
    L_intrede: float,
    L_but: float,
    # Boundary condition parameters
    buitenwaterstand: float,
    buitenwaterstand_gemiddeld: float,
    polderpeil: float,
    mv_exit: float,
    # Subsoil property parameters
    phi_exit_gemiddeld: float,
    r_exit: float,
    top_zand: float,
    kv_voorland: float,
    k_wvp: float,
    D_wvp: float,
    d70: float,
    gamma_sat_deklaag: float,
    # Model property parameters
    modelfactor_u: float,
    modelfactor_h: float,
    modelfactor_p: float,
    modelfactor_ff: float,
    modelfactor_3d: float,
    modelfactor_aniso: float,
    modelfactor_ml: float,
    i_c_h: float,
    r_c_deklaag: float,
    d70_m: float,
    gamma_korrel: float,
    v: float,
    theta: float,
    eta: float,
    # Constants
    g: float,
    gamma_water: float,
) -> tuple[float, ...]:
    """Grenstoestandsfuncties volgens het WBI-model met
    grondwaterstroming conform MORIA model. Met aanpassing van meebepalen
    van lambda_voorland. Omdat er op dit moment geen gevalideerd geohydrologisch
    model.

    :param L_intrede:
    :param L_but:
    :param buitenwaterstand:
    :param buitenwaterstand_gemiddeld:
    :param polderpeil:
    :param mv_exit:
    :param phi_exit_gemiddeld:
    :param r_exit:
    :param top_zand:
    :param k_wvp:
    :param D_wvp:
    :param d70:
    :param gamma_sat_deklaag:
    :param modelfactor_u:
    :param modelfactor_h:
    :param modelfactor_p:
    :param modelfactor_ff: Model factor fijne fractie.
    :param modelfactor_3d: Model factor 3D effecten.
    :param modelfactor_aniso: Model factor anisotropie.
    :param modelfactor_ml: Model factor meerlaagsheid zandpakket.
    :param i_c_h:
    :param r_c_deklaag:
    :param d70_m:
    :param gamma_korrel:
    :param v:
    :param theta:
    :param eta:
    :param g:
    :param gamma_water:
    :return:
    """
    d_deklaag = pc_piping.calc_d_deklaag(mv_exit=mv_exit, top_zand=top_zand)
    # TODO: maak kv_voorland een parameter
    c_voorland = d_deklaag / kv_voorland
    kD_wvp = k_wvp * D_wvp
    lambda_voorland = pc_piping.calc_lambda_voorland(
        kD_wvp=kD_wvp, c_voorland=c_voorland
    )

    L_voorland = pc_piping.calc_lengte_voorland(L_intrede=L_intrede, L_but=L_but)
    W_voorland = pc_piping.calc_W_voorland(
        lambda_voorland=lambda_voorland, L_voorland=L_voorland
    )
    L_kwelweg = pc_piping.calc_L_kwelweg(L_but=L_but, W_voorland=W_voorland)
    h_exit = pc_piping.calc_h_exit(polderpeil=polderpeil, mv_exit=mv_exit)

    phi_exit = phi_exit_gemiddeld + r_exit * (
        buitenwaterstand - buitenwaterstand_gemiddeld
    )
    dphi_c_u = pc_piping.calc_dphi_c_u(
        d_deklaag=d_deklaag,
        gamma_sat_deklaag=gamma_sat_deklaag,
        gamma_water=gamma_water,
    )
    i_exit = pc_piping.calc_i_exit(
        phi_exit=phi_exit, h_exit=h_exit, d_deklaag=d_deklaag
    )
    dh_c = pc_piping.calc_dh_c(
        d70=d70,
        D_wvp=D_wvp,
        kD_wvp=kD_wvp,
        L_kwelweg=L_kwelweg,
        gamma_water=gamma_water,
        g=g,
        v=v,
        theta=theta,
        eta=eta,
        d70_m=d70_m,
        gamma_korrel=gamma_korrel,
    )
    dh_red = pc_piping.calc_dh_red(
        buitenwaterstand=buitenwaterstand,
        h_exit=h_exit,
        r_c_deklaag=r_c_deklaag,
        d_deklaag=d_deklaag,
    )
    z_u = modelfactor_u * dphi_c_u - (phi_exit - h_exit)
    z_h = (modelfactor_h * i_c_h) - i_exit
    z_p = (
        modelfactor_p
        * modelfactor_ff
        * modelfactor_3d
        * modelfactor_aniso
        * modelfactor_ml
        * dh_c
    ) - dh_red
    z_combin = max(z_u, z_h, z_p)

    return (
        z_u,
        z_h,
        z_p,
        z_combin,
        h_exit,
        phi_exit,
        d_deklaag,
        dphi_c_u,
        i_exit,
        lambda_voorland,
        L_voorland,
        W_voorland,
        L_kwelweg,
        kD_wvp,
        dh_c,
        dh_red,
    )


# noinspection PyPep8Naming
def calc_Z_u(
    # Geometry parameters
    L_intrede: float,
    L_but: float,
    # Boundary condition parameters
    buitenwaterstand: float,
    buitenwaterstand_gemiddeld: float,
    polderpeil: float,
    mv_exit: float,
    # Subsoil property parameters
    phi_exit_gemiddeld: float,
    top_zand: float,
    r_exit: float,
    kv_voorland: float,
    k_wvp: float,
    D_wvp: float,
    d70: float,
    gamma_sat_deklaag: float,
    # Model property parameters
    modelfactor_u: float,
    modelfactor_h: float,
    modelfactor_p: float,
    modelfactor_ff: float,
    modelfactor_3d: float,
    modelfactor_aniso: float,
    modelfactor_ml: float,
    i_c_h: float,
    r_c_deklaag: float,
    # Overige parameters
    gamma_water: float,
    # Constants  # TODO: Ombouwen tot globals
    d70_m: float,
    gamma_korrel: float,
    v: float,
    theta: float,
    eta: float,
    g: float,
) -> float:
    r"""Grenstoestandfunctie voor opbarsten (uplift).

    Returns:
        float: Z waarde van de grenstoestandfunctie voor opbarsten
    """
    return limit_state_wshd(
        buitenwaterstand=buitenwaterstand,
        buitenwaterstand_gemiddeld=buitenwaterstand_gemiddeld,
        polderpeil=polderpeil,
        mv_exit=mv_exit,
        top_zand=top_zand,
        r_exit=r_exit,
        kv_voorland=kv_voorland,
        k_wvp=k_wvp,
        D_wvp=D_wvp,
        d70=d70,
        gamma_sat_deklaag=gamma_sat_deklaag,
        modelfactor_u=modelfactor_u,
        modelfactor_h=modelfactor_h,
        modelfactor_p=modelfactor_p,
        modelfactor_ff=modelfactor_ff,
        modelfactor_3d=modelfactor_3d,
        modelfactor_aniso=modelfactor_aniso,
        modelfactor_ml=modelfactor_ml,
        i_c_h=i_c_h,
        r_c_deklaag=r_c_deklaag,
        gamma_water=gamma_water,
        d70_m=d70_m,
        gamma_korrel=gamma_korrel,
        v=v,
        theta=theta,
        eta=eta,
        g=g,
        L_intrede=L_intrede,
        L_but=L_but,
        phi_exit_gemiddeld=phi_exit_gemiddeld,
    )[0]


# noinspection PyPep8Naming
def calc_Z_h(
    # Geometry parameters
    L_intrede: float,
    L_but: float,
    # Boundary condition parameters
    buitenwaterstand: float,
    buitenwaterstand_gemiddeld: float,
    polderpeil: float,
    mv_exit: float,
    # Subsoil property parameters
    phi_exit_gemiddeld: float,
    top_zand: float,
    r_exit: float,
    kv_voorland: float,
    k_wvp: float,
    D_wvp: float,
    d70: float,
    gamma_sat_deklaag: float,
    # Model property parameters
    modelfactor_u: float,
    modelfactor_h: float,
    modelfactor_p: float,
    modelfactor_ff: float,
    modelfactor_3d: float,
    modelfactor_aniso: float,
    modelfactor_ml: float,
    i_c_h: float,
    r_c_deklaag: float,
    # Overige parameters
    gamma_water: float,
    # Constants  # TODO: Ombouwen tot globals
    d70_m: float,
    gamma_korrel: float,
    v: float,
    theta: float,
    eta: float,
    g: float,
) -> float:
    r"""Wrapper over de grenstoestandfunctie voor heave zodat deze bruikbaar is voor de Probabilistic Library.

    Returns:
        float: Z waarde van de grenstoestandfunctie voor heave
    """
    return limit_state_wshd(
        buitenwaterstand=buitenwaterstand,
        buitenwaterstand_gemiddeld=buitenwaterstand_gemiddeld,
        polderpeil=polderpeil,
        mv_exit=mv_exit,
        top_zand=top_zand,
        r_exit=r_exit,
        kv_voorland=kv_voorland,
        k_wvp=k_wvp,
        D_wvp=D_wvp,
        d70=d70,
        gamma_sat_deklaag=gamma_sat_deklaag,
        modelfactor_u=modelfactor_u,
        modelfactor_h=modelfactor_h,
        modelfactor_p=modelfactor_p,
        modelfactor_ff=modelfactor_ff,
        modelfactor_3d=modelfactor_3d,
        modelfactor_aniso=modelfactor_aniso,
        modelfactor_ml=modelfactor_ml,
        i_c_h=i_c_h,
        r_c_deklaag=r_c_deklaag,
        gamma_water=gamma_water,
        d70_m=d70_m,
        gamma_korrel=gamma_korrel,
        v=v,
        theta=theta,
        eta=eta,
        g=g,
        L_intrede=L_intrede,
        L_but=L_but,
        phi_exit_gemiddeld=phi_exit_gemiddeld,
    )[1]


# noinspection PyPep8Naming
def calc_Z_p(
    # Geometry parameters
    L_intrede: float,
    L_but: float,
    # Boundary condition parameters
    buitenwaterstand: float,
    buitenwaterstand_gemiddeld: float,
    polderpeil: float,
    mv_exit: float,
    # Subsoil property parameters
    phi_exit_gemiddeld: float,
    top_zand: float,
    r_exit: float,
    kv_voorland: float,
    k_wvp: float,
    D_wvp: float,
    d70: float,
    gamma_sat_deklaag: float,
    # Model property parameters
    modelfactor_u: float,
    modelfactor_h: float,
    modelfactor_p: float,
    modelfactor_ff: float,
    modelfactor_3d: float,
    modelfactor_aniso: float,
    modelfactor_ml: float,
    i_c_h: float,
    r_c_deklaag: float,
    # Overige parameters
    gamma_water: float,
    # Constants  # TODO: Ombouwen tot globals
    d70_m: float,
    gamma_korrel: float,
    v: float,
    theta: float,
    eta: float,
    g: float,
) -> float:
    r"""Grenstoestandfunctie voor het mechanisme terugschrijdende erosie (piping).

    Returns:
        float: Z waarde van de grenstoestandfunctie voor piping
    """
    return limit_state_wshd(
        buitenwaterstand=buitenwaterstand,
        buitenwaterstand_gemiddeld=buitenwaterstand_gemiddeld,
        polderpeil=polderpeil,
        mv_exit=mv_exit,
        top_zand=top_zand,
        r_exit=r_exit,
        kv_voorland=kv_voorland,
        k_wvp=k_wvp,
        D_wvp=D_wvp,
        d70=d70,
        gamma_sat_deklaag=gamma_sat_deklaag,
        modelfactor_u=modelfactor_u,
        modelfactor_h=modelfactor_h,
        modelfactor_p=modelfactor_p,
        modelfactor_ff=modelfactor_ff,
        modelfactor_3d=modelfactor_3d,
        modelfactor_aniso=modelfactor_aniso,
        modelfactor_ml=modelfactor_ml,
        i_c_h=i_c_h,
        r_c_deklaag=r_c_deklaag,
        gamma_water=gamma_water,
        d70_m=d70_m,
        gamma_korrel=gamma_korrel,
        v=v,
        theta=theta,
        eta=eta,
        g=g,
        L_intrede=L_intrede,
        L_but=L_but,
        phi_exit_gemiddeld=phi_exit_gemiddeld,
    )[2]


# noinspection PyPep8Naming
def calc_Z_project(
    # Geometry parameters
    L_intrede: float,
    L_but: float,
    # Boundary condition parameters
    buitenwaterstand: float,
    buitenwaterstand_gemiddeld: float,
    polderpeil: float,
    mv_exit: float,
    # Subsoil property parameters
    phi_exit_gemiddeld: float,
    top_zand: float,
    r_exit: float,
    kv_voorland: float,
    k_wvp: float,
    D_wvp: float,
    d70: float,
    gamma_sat_deklaag: float,
    # Model property parameters
    modelfactor_u: float,
    modelfactor_h: float,
    modelfactor_p: float,
    modelfactor_ff: float,
    modelfactor_3d: float,
    modelfactor_aniso: float,
    modelfactor_ml: float,
    i_c_h: float,
    r_c_deklaag: float,
    # Overige parameters
    gamma_water: float,
    # Constants  # TODO: Ombouwen tot globals
    d70_m: float,
    gamma_korrel: float,
    v: float,
    theta: float,
    eta: float,
    g: float,
) -> float:
    r"""Grenstoestandfunctie voor het mechanisme piping. Deze grenstoestandfunctie bepaalt de Z waarde
    op basis van de afzonderlijke Z waarden van de mechanismen uplift, heave en terugschrijdende erosie door
    max(Z_u, Z_h, Z_p).

    Returns:
        float: Z waarde van de grenstoestandfunctie voor piping
    """
    return limit_state_wshd(
        buitenwaterstand=buitenwaterstand,
        buitenwaterstand_gemiddeld=buitenwaterstand_gemiddeld,
        polderpeil=polderpeil,
        mv_exit=mv_exit,
        top_zand=top_zand,
        r_exit=r_exit,
        kv_voorland=kv_voorland,
        k_wvp=k_wvp,
        D_wvp=D_wvp,
        d70=d70,
        gamma_sat_deklaag=gamma_sat_deklaag,
        modelfactor_u=modelfactor_u,
        modelfactor_h=modelfactor_h,
        modelfactor_p=modelfactor_p,
        modelfactor_ff=modelfactor_ff,
        modelfactor_3d=modelfactor_3d,
        modelfactor_aniso=modelfactor_aniso,
        modelfactor_ml=modelfactor_ml,
        i_c_h=i_c_h,
        r_c_deklaag=r_c_deklaag,
        gamma_water=gamma_water,
        d70_m=d70_m,
        gamma_korrel=gamma_korrel,
        v=v,
        theta=theta,
        eta=eta,
        g=g,
        L_intrede=L_intrede,
        L_but=L_but,
        phi_exit_gemiddeld=phi_exit_gemiddeld,
    )[3]


MODEL_NAMES = {
    calc_Z_u.__name__: "Uplift",
    calc_Z_h.__name__: "Heave",
    calc_Z_p.__name__: "Piping",
}
