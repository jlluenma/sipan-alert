from sipan.official_alerts import match_alerts

def test_name_match_is_not_identity_confirmation():
    matches=match_alerts('Yapi Cash ofrece un prestamo')
    assert len(matches)==1
    assert 'identidad por confirmar' in matches[0]['status']
    assert matches[0]['source'].startswith('SBS')

def test_package_match():
    matches=match_alerts('App com.yapi.peru.prestamo')
    assert matches[0]['status']=='Identificador coincidente'

def test_unlisted_is_not_accused():
    assert match_alerts('Oferta de una empresa desconocida')==[]
    assert match_alerts('yapi cashmere')==[]
