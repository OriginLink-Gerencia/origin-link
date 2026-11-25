import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import Proveedores from './pages/Proveedores';
import Vinculos from './pages/Vinculos';
import { crearProveedor, invitarProveedor, listarProveedores, listarVinculos } from './lib/api';

jest.mock('./lib/api', () => ({
  listarProveedores: jest.fn(),
  crearProveedor: jest.fn(),
  actualizarProveedor: jest.fn(),
  invitarProveedor: jest.fn(),
  listarVinculos: jest.fn(),
  ApiError: class extends Error { status = 0; },
}));

const listado = listarProveedores as jest.Mock;
const crear = crearProveedor as jest.Mock;
const invitar = invitarProveedor as jest.Mock;
const vinculos = listarVinculos as jest.Mock;
const proveedor = {
  id: 1,
  nombre: 'Cooperativa Jaén',
  region: 'Cajamarca',
  contacto_nombre: null,
  contacto_telefono: null,
  contacto_email: null,
  estado_vinculo: 'SIN_VINCULAR',
  organizacion_proveedora_id: null,
  creado_en: new Date().toISOString(),
};

beforeEach(() => {
  jest.clearAllMocks();
  listado.mockResolvedValue([]);
  crear.mockResolvedValue(proveedor);
  invitar.mockResolvedValue({
    token: 'token-prueba',
    url: 'http://localhost:5173/invitacion/token-prueba',
    expira_en: new Date(Date.now() + 86400000).toISOString(),
  });
  vinculos.mockResolvedValue([]);
});

test('HU-05 registra un proveedor y actualiza el directorio', async () => {
  render(<Proveedores />);
  await screen.findByText('Aún no tienes proveedores registrados.');
  listado.mockResolvedValue([proveedor]);
  fireEvent.change(screen.getByLabelText(/nombre del proveedor/i), {
    target: { value: 'Cooperativa Jaén' },
  });
  fireEvent.click(screen.getByRole('button', { name: /^registrar proveedor$/i }));
  await waitFor(() => expect(crear).toHaveBeenCalledWith(
    expect.objectContaining({ nombre: 'Cooperativa Jaén' }),
  ));
  expect(await screen.findByText('Proveedor registrado correctamente.')).toBeInTheDocument();
  expect(await screen.findByRole('heading', { name: 'Cooperativa Jaén' })).toBeInTheDocument();
});

test('HU-06 permite generar la invitación y muestra su enlace', async () => {
  listado.mockResolvedValue([proveedor]);
  render(<Proveedores />);
  await screen.findByRole('heading', { name: 'Cooperativa Jaén' });
  fireEvent.click(screen.getByRole('button', { name: 'Invitar' }));
  await waitFor(() => expect(invitar).toHaveBeenCalledWith(1));
  expect(await screen.findByLabelText('Enlace de invitación')).toHaveValue(
    'http://localhost:5173/invitacion/token-prueba',
  );
});

test('HU-07 muestra los vínculos de la cooperativa', async () => {
  vinculos.mockResolvedValue([{
    tostador_id: 2,
    tostador: 'Tostaduría A',
    vinculado_desde: new Date().toISOString(),
  }]);
  render(<Vinculos />);
  expect(await screen.findByRole('heading', { name: 'Tostaduría A' })).toBeInTheDocument();
  expect(vinculos).toHaveBeenCalledTimes(1);
});
